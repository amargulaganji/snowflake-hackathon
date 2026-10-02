---
created: 2026-09-30T00:00:00.000Z
session: 99bf18ce-cc31-4e7c-9455-db243a5bea4b
working_directory: C:\Users\mmgul\Desktop\Amar\Projects\snowflake-hackathon
---

# Member 360 + Clinical/Regulatory Document Copilot — Implementation Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript)              nginx :80           │
│  Member search sidebar → Chat/query panel → Evidence chain display   │
│  Kite theme: #F7F9FB bg, #387ED1 accent, card-based, data-dense     │
├──────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                 uvicorn :8000       │
│  GET /members  GET /members/{id}  POST /ask                          │
│  Wraps Cortex Agent REST API only — no direct table access           │
├──────────────────────────────────────────────────────────────────────┤
│  Snowflake Cortex Agent                                              │
│  Tools: cortex_analyst (semantic view) + cortex_search ×3            │
│         + score_polypharmacy_risk UDF + check_policy_compliance UDF  │
│  Guardrails: evidence-chain, decline-when-uncertain, contradiction   │
├──────────────────────────────────────────────────────────────────────┤
│  Snowflake Data Layer                                                │
│  Structured: Member, Encounter, Medication, Diagnosis, LabResult     │
│  Unstructured: ClinicalNote, PolicyDocument, DrugInteractionGuideline│
│  Semantic View over structured tables                                │
│  3 Cortex Search Services over unstructured tables                   │
└──────────────────────────────────────────────────────────────────────┘
```

## Step 1: SQL Layer (sql/ directory — 8 files)

All SQL files go in `sql/` at the project root.

### sql/01_setup.sql
- CREATE DATABASE IF NOT EXISTS CLINICAL_COPILOT
- CREATE SCHEMA IF NOT EXISTS CLINICAL_COPILOT.CORE
- CREATE OR REPLACE WAREHOUSE COPILOT_WH WITH WAREHOUSE_SIZE='SMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE
- USE DATABASE/SCHEMA/WAREHOUSE statements

### sql/02_structured_tables.sql
Tables (all in CLINICAL_COPILOT.CORE):
- **MEMBER**: member_id (VARCHAR PK), first_name, last_name, dob (DATE), age (INT), gender, plan_type, enrollment_date, pcp_name, risk_flags (VARIANT — array of strings)
- **ENCOUNTER**: encounter_id (VARCHAR PK), member_id FK, encounter_date (DATE), encounter_type (inpatient/outpatient/ER/telehealth), provider_name, facility, primary_diagnosis_code, notes_summary, notes_doc_id
- **MEDICATION**: medication_id (VARCHAR PK), member_id FK, drug_name, ndc_code, dosage, route, frequency, start_date, end_date, prescriber, status (active/discontinued/on-hold)
- **DIAGNOSIS**: diagnosis_id (VARCHAR PK), member_id FK, icd10_code, description, diagnosed_date, status (active/resolved/chronic), diagnosing_provider
- **LAB_RESULT**: lab_id (VARCHAR PK), member_id FK, test_name, loinc_code, result_value (FLOAT), unit, reference_range_low (FLOAT), reference_range_high (FLOAT), result_date, abnormal_flag (BOOLEAN)

### sql/03_unstructured_tables.sql
- **CLINICAL_NOTE**: note_id (VARCHAR PK), member_id, encounter_id, note_date, note_type (progress/discharge/consult/referral), author, content_text (VARCHAR — full clinical narrative)
- **POLICY_DOCUMENT**: doc_id (VARCHAR PK), policy_name, category (formulary/prior-auth/step-therapy/coverage), source, topic, effective_date, content_text
- **DRUG_INTERACTION_GUIDELINE**: guideline_id (VARCHAR PK), drug_pair (VARCHAR — "DrugA + DrugB"), severity (minor/moderate/major/contraindicated), source, description, content_text

### sql/04_synthetic_data.sql
Generate realistic synthetic data:
- 50 members with varied demographics (elderly focus for polypharmacy demo)
- ~200 encounters across members
- ~300 medications (ensure some members have 5+ active → polypharmacy)
- ~400 diagnoses with real ICD-10 codes
- ~500 lab results with some abnormal flags
- ~100 clinical notes with realistic narrative text including:
  - At least 2 notes that contradict structured data (e.g., note says "NKDA" but allergy in diagnosis, note says "continues metformin" but medication table shows discontinued)
- ~30 policy documents (formulary rules, prior auth criteria, step therapy protocols)
- ~50 drug interaction guidelines with severity levels

### sql/05_semantic_view.yaml
Semantic view YAML for CLINICAL_COPILOT.CORE.CLINICAL_SEMANTIC_VIEW:
- Logical tables: Members, Encounters, Medications, Diagnoses, LabResults
- Dimensions: member_name (first+last), gender, plan_type, drug_name, icd10_code, encounter_type, test_name, diagnosis_status, medication_status
- Facts: age, dosage, result_value, abnormal_flag
- Metrics:
  - active_medication_count: COUNT of medications WHERE status='active' per member
  - polypharmacy_flag: CASE WHEN active_medication_count >= 5 THEN TRUE
  - abnormal_lab_count: COUNT of lab results WHERE abnormal_flag=TRUE per member
  - encounter_frequency_90d: COUNT encounters in last 90 days per member
- Relationships: Member→Encounter (member_id), Member→Medication (member_id), Member→Diagnosis (member_id), Member→LabResult (member_id), Encounter→ClinicalNote (encounter_id)
- Verified queries: 8-10 common questions
- Custom instructions for the agent about business domain

Also include `sql/05_create_semantic_view.sql` that calls SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML.

### sql/06_cortex_search.sql
Three Cortex Search services:
1. CLINICAL_NOTES_SEARCH — ON content_text, ATTRIBUTES: member_id, note_type, note_date; warehouse=COPILOT_WH, TARGET_LAG='1 hour'
2. POLICY_DOCS_SEARCH — ON content_text, ATTRIBUTES: category, policy_name, topic; warehouse=COPILOT_WH, TARGET_LAG='1 day'
3. DRUG_INTERACTION_SEARCH — ON content_text, ATTRIBUTES: drug_pair, severity; warehouse=COPILOT_WH, TARGET_LAG='1 day'

### sql/07_udfs.sql
Two SQL UDFs returning VARIANT:
1. **SCORE_POLYPHARMACY_RISK(p_member_id VARCHAR)** — queries MEDICATION + DRUG_INTERACTION_GUIDELINE, returns { risk_level, active_med_count, flagged_interactions: [{drug_pair, severity, description}], reasoning }
2. **CHECK_POLICY_COMPLIANCE(p_member_id VARCHAR, p_drug_name VARCHAR)** — queries MEDICATION + POLICY_DOCUMENT, returns { compliant, policy_name, requirements: [], gaps: [], reasoning }

### sql/08_agent.sql
CREATE AGENT CLINICAL_COPILOT.CORE.CLINICAL_COPILOT_AGENT with:
- Tools: cortex_analyst_text_to_sql, 3× cortex_search, 2× generic (UDFs)
- tool_resources linking each tool to its service/UDF
- Instructions (response + orchestration) implementing all 4 guardrails
- Orchestration budget (seconds: 60, tokens: 32000)
- Analytical search enabled

#### Context Sources
- Snowflake docs: Cortex Agent REST API spec, CREATE AGENT syntax, Semantic View YAML spec, CREATE CORTEX SEARCH SERVICE syntax
- User spec: entity definitions, relationships, guardrail requirements, demo scenario

---

## Step 2: FastAPI Backend (backend/ directory)

### backend/requirements.txt
fastapi, uvicorn[standard], httpx, pydantic, pydantic-settings, python-dotenv

### backend/.env.example
SNOWFLAKE_ACCOUNT_URL, SNOWFLAKE_PAT, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_AGENT_NAME, SNOWFLAKE_WAREHOUSE

### backend/app/config.py
Pydantic Settings class loading from environment variables.

### backend/app/auth.py
Helper to build Authorization header from PAT token.

### backend/app/models/schemas.py
Pydantic models:
- MemberSummary (id, first_name, last_name, age, gender, plan_type, risk_flags)
- MemberDetail (extends summary with encounters, medications, diagnoses, labs)
- AskRequest (member_id, question)
- EvidenceItem (source_type, source_name, content, relevance)
- AskResponse (answer, evidence_chain: list[EvidenceItem], risk_level, contradiction_detected, contradiction_details, insufficient_evidence)

### backend/app/services/snowflake_client.py
- CortexAgentClient class wrapping httpx.AsyncClient
- run_agent(messages, stream=False) → calls POST /api/v2/databases/{db}/schemas/{schema}/agents/{name}:run
- Uses PAT auth header

### backend/app/services/response_parser.py
- parse_agent_response(raw_response) → AskResponse
- Extracts text blocks, tool-use/tool-result blocks
- Builds evidence chain from tool results
- Detects risk_level from tool results (score_polypharmacy_risk output)
- Detects contradictions from agent text or multi-tool comparison
- Detects insufficient_evidence from agent decline patterns

### backend/app/routers/members.py
- GET /members?q={search_term} — sends "List members matching '{q}'" to agent, parses structured result
- GET /members/{member_id} — sends "Show full profile for member {id}" to agent

### backend/app/routers/agent.py
- POST /ask — accepts AskRequest, prepends member context, calls agent, returns AskResponse

### backend/app/main.py
- FastAPI app with CORS (allow frontend origin)
- Include routers
- Health check endpoint GET /health

### backend/Dockerfile
python:3.11-slim, pip install requirements.txt, uvicorn app.main:app --host 0.0.0.0 --port 8000

#### Context Sources
- Snowflake docs: Cortex Agents Run API (POST agent:run), SSE streaming format, response schema with tool-use/tool-result blocks
- User spec: endpoint design (GET /members, GET /members/{id}, POST /ask), no direct Snowflake access from app layer

---

## Step 3: React Frontend (frontend/ directory)

### Project setup
Vite + React + TypeScript. Package deps: react, react-dom, axios.

### Theme (Zerodha Kite-inspired, LIGHT variant per user spec)
- Background: #F7F9FB
- Surface: #FFFFFF
- Accent: #387ED1
- Text: #212121 primary, #757575 secondary
- Risk: low=#2E7D32, moderate=#B26A00, high=#C62828
- Font: Inter/system sans-serif
- Card-based layout, minimal chrome, data-dense

### frontend/src/types/index.ts
TypeScript interfaces mirroring backend schemas.

### frontend/src/api/client.ts
Axios instance with baseURL from env (VITE_API_URL), typed request functions.

### frontend/src/hooks/useMemberSearch.ts
Debounced search hook calling GET /members?q=...

### frontend/src/hooks/useAgent.ts
Hook calling POST /ask, managing loading/error/response state.

### frontend/src/components/Layout.tsx
Two-column layout: left sidebar (member search + profile), right main panel (chat/query).

### frontend/src/components/MemberSearch.tsx
Search input with dropdown results. Click to select.

### frontend/src/components/MemberProfile.tsx
Card showing selected member: name, age, gender, plan_type, risk_flags badges.

### frontend/src/components/ChatPanel.tsx
Question input at bottom, message thread above. Each message is a ChatMessage.

### frontend/src/components/ChatMessage.tsx
User question or AI response bubble. AI responses include EvidenceChain, RiskBadge, ContradictionBanner.

### frontend/src/components/EvidenceChain.tsx
Collapsible accordion. Each item: source icon + type label + content excerpt. Structured fields on left, document snippets on right.

### frontend/src/components/RiskBadge.tsx
Pill/badge: "Low Risk" green, "Moderate Risk" amber, "High Risk" red.

### frontend/src/components/ContradictionBanner.tsx
Alert banner in red/amber: "Contradiction Detected: {details}". Only shown when contradiction_detected=true.

### frontend/src/App.tsx
Root component composing Layout with state management.

### frontend/src/main.tsx
ReactDOM.createRoot entry point.

### frontend/src/styles/globals.css
CSS variables for theme, reset, typography, utility classes.

### frontend/Dockerfile
Multi-stage: node:20-alpine build → nginx:alpine serve, port 80.

### frontend/vite.config.ts
Dev proxy to backend, build output config.

#### Context Sources
- User spec: theme colors, component list, UX flow, card-based layout
- Architecture: frontend calls backend only, never Snowflake directly

---

## Step 4: Docker & Project Config

### docker-compose.yml (project root)
Two services:
- backend: build ./backend, port 8000:8000, env_file .env, healthcheck
- frontend: build ./frontend, port 3000:80, depends_on backend, env VITE_API_URL=http://backend:8000

### .env.example (project root)
Template for all required environment variables.

### .gitignore
Node_modules, __pycache__, .env, dist/, build/

### README.md
Updated with project description, architecture diagram, setup instructions, environment variables, how to run with docker-compose.

---

## Verification
- All SQL files parse correctly (syntax validation)
- Backend starts without errors (uvicorn loads)
- Frontend builds without errors (vite build)
- Docker images build successfully
- docker-compose up brings both services up and frontend can reach backend /health
