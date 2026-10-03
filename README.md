# SnowCare360

**Member 360 + Clinical/Regulatory Document Copilot**

A Snowflake-native healthcare intelligence platform that combines structured clinical data with unstructured documents through a 7-tool Cortex Agent. Built entirely on Snowflake — every byte of data, every AI inference, every search query, every scheduled job, and the application itself runs inside the Snowflake security perimeter.

---

## What It Does

SnowCare360 gives care management teams a single view of each member's clinical profile, medication risks, policy compliance gaps, and supporting evidence. A care manager can:

- Search members and see precomputed risk summaries powered by a Dynamic Table
- Ask natural language questions and get evidence-grounded answers with numbered citations
- Click any citation to open the Evidence Inspector showing the exact source
- Upload clinical or regulatory documents that become searchable within minutes
- View a lane-based clinical timeline spanning encounters, medications, diagnoses, labs, claims, and documents
- Create synthetic members for testing via Member Studio
- Review every AI interaction in a full audit trail
- Monitor scheduled Snowflake tasks and their execution history

---

## Snowflake Platform Usage

Every major Snowflake capability is used meaningfully, not for demonstration count:

| Snowflake Capability | Object(s) | Purpose |
|---------------------|-----------|---------|
| **Cortex Agent** | `CLINICAL_COPILOT_AGENT` (7 tools) | Agentic RAG: routes questions to the right tools, cross-validates, cites sources |
| **Cortex Analyst** | `CLINICAL_SEMANTIC_VIEW` (8 verified queries) | NL-to-SQL over 5 clinical tables with dimension/metric ontology |
| **Cortex Search** | 4 services (clinical notes, policies, drug interactions, uploaded documents) | Hybrid vector + keyword retrieval for unstructured content |
| **Dynamic Table** | `MEMBER_360_SUMMARY` (TARGET_LAG 1hr) | Precomputed per-member aggregates avoiding expensive joins on every page load |
| **Streams** | 3 (DOCUMENT, MEDICATION, LAB_RESULT change streams) | Incremental CDC for triggering downstream processing |
| **Tasks** | `RISK_DELTA_NIGHTLY_TASK` (cron daily), `DOCUMENT_PROCESSING_TASK` (stream-triggered) | Automated risk recomputation and document indexing |
| **Stages** | `DOCUMENT_STAGE`, `STREAMLIT_STAGE` (internal, SSE encrypted) | Snowflake-native file storage for uploads and Streamlit code |
| **UDFs** | `SCORE_POLYPHARMACY_RISK`, `CHECK_POLICY_COMPLIANCE` | Deterministic clinical risk scoring registered as agent tools |
| **Stored Procedure** | `REFRESH_RISK_DELTAS` | Computes risk score changes, writes to RISK_DELTA_LOG |
| **Streamlit-in-Snowflake** | `SnowCare360_DASHBOARD` | Population health analytics dashboard accessible in Snowsight |
| **SPCS** | `COPILOT_SERVICE` on `COPILOT_COMPUTE_POOL` (CPU_X64_S) | Hosts the React + FastAPI app containers inside Snowflake |
| **Semantic View** | `CLINICAL_SEMANTIC_VIEW` | 5-table ontology with verified queries for Cortex Analyst |

Full inventory: [docs/architecture/SNOWFLAKE_RESOURCE_MAP.md](docs/architecture/SNOWFLAKE_RESOURCE_MAP.md) (36 total Snowflake objects)

---

## Architecture

```
+----------------------------------------------------------------------+
|  Frontend (React 18 + TypeScript + Vite)                 nginx :80   |
|  Persistent left nav | Member 360 (10 tabs) | Agent chat | Evidence  |
|  Inspector | Document upload | Member Studio | Audit | Jobs          |
+----------------------------------------------------------------------+
|  Backend (FastAPI + Python 3.11)                      uvicorn :8000  |
|  5 routers: members, agent, documents, studio, admin                 |
|  Role-based auth | Audit logging | Citation resolution               |
+----------------------------------------------------------------------+
|  Snowflake Cortex Agent (7 tools)                                    |
|  Cortex Analyst | 4x Cortex Search | 2x UDFs                        |
|  Guardrails: evidence-only, contradiction detection, decline-if-uncertain |
+----------------------------------------------------------------------+
|  Snowflake Data Layer                                                |
|  15 tables | 1 Dynamic Table | 1 Semantic View | 4 Search Services  |
|  3 Streams | 2 Tasks | 2 Stages | 1 Stored Procedure                |
|  1 Streamlit App | SPCS (Compute Pool + Service + Image Repo)       |
+----------------------------------------------------------------------+
```

Architecture decisions: [docs/coco/02_architecture.md](docs/coco/02_architecture.md)

---

## Quick Start (Local with Docker)

### Prerequisites

- Docker Desktop with Docker Compose
- Snowflake account with Cortex Agent access (Enterprise edition or higher)
- Snowflake Programmatic Access Token (PAT)

### 1. Clone the repository

```bash
git clone <repo-url>
cd snowflake-hackathon
```

### 2. Run SQL setup scripts

Execute the SQL files in `sql/` **in order** against your Snowflake account. You can run them in Snowsight worksheets or via SnowSQL.

| Script | What It Creates |
|--------|----------------|
| `sql/01_setup.sql` | Database `CLINICAL_COPILOT`, schema `CORE`, warehouse `COPILOT_WH` |
| `sql/02_structured_tables.sql` | Core clinical tables (MEMBER, ENCOUNTER, MEDICATION, DIAGNOSIS, LAB_RESULT, CLAIM, ATTACHMENT) |
| `sql/03_unstructured_tables.sql` | Knowledge base tables (CLINICAL_NOTE, POLICY_DOCUMENT, DRUG_INTERACTION_GUIDELINE) + system tables (DOCUMENT, DOCUMENT_CHUNK, AI_AUDIT_LOG, APP_USER, RISK_DELTA_LOG) + Dynamic Table + Streams + Stages |
| `sql/04_synthetic_data.sql` | 50 synthetic members + 596 clinical records across all tables |
| `sql/05_create_semantic_view.sql` | `CLINICAL_SEMANTIC_VIEW` with dimensions, metrics, and 8 verified queries |
| `sql/06_cortex_search.sql` | 4 Cortex Search services (clinical notes, policies, drug interactions, document search) |
| `sql/07_udfs.sql` | 2 UDFs (`SCORE_POLYPHARMACY_RISK`, `CHECK_POLICY_COMPLIANCE`) + stored procedure + tasks |
| `sql/08_agent.sql` | `CLINICAL_COPILOT_AGENT` with 7 tools (YAML spec format) |
| `sql/09_deploy_spcs.sql` | SPCS compute pool, image repository, service spec (for cloud deployment) |
| `sql/10_streamlit.sql` | Streamlit-in-Snowflake dashboard |

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your Snowflake credentials:

```env
# Required
SNOWFLAKE_ACCOUNT_URL=https://<orgname>-<accountname>.snowflakecomputing.com
SNOWFLAKE_PAT=<your-programmatic-access-token>

# Optional (defaults shown)
SNOWFLAKE_DATABASE=CLINICAL_COPILOT
SNOWFLAKE_SCHEMA=CORE
SNOWFLAKE_AGENT_NAME=CLINICAL_COPILOT_AGENT
SNOWFLAKE_WAREHOUSE=COPILOT_WH
```

**How to get a PAT**: In Snowsight, go to your user menu (bottom-left) > Settings > Authentication > Programmatic Access Tokens > Create Token. Give it a name, set the role to `ACCOUNTADMIN` (or a role with access to `CLINICAL_COPILOT`), and copy the token value.

### 4. Build and run

```bash
docker compose up --build -d
```

### 5. Verify

```bash
# Backend health check
curl http://localhost:8000/health

# Open the UI
open http://localhost:3000
```

| Service | URL |
|---------|-----|
| Frontend (React app) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Health check | http://localhost:8000/health |

### 6. Run tests

```bash
python -m tests.test_error_handling
python -m tests.test_new_endpoints
python -m tests.test_guardrails
```

Requires `httpx` installed locally: `pip install httpx`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SNOWFLAKE_ACCOUNT_URL` | Yes | — | Full Snowflake account URL (e.g., `https://orgname-acctname.snowflakecomputing.com`) |
| `SNOWFLAKE_PAT` | Yes | — | Programmatic Access Token for authentication |
| `SNOWFLAKE_DATABASE` | No | `CLINICAL_COPILOT` | Database name |
| `SNOWFLAKE_SCHEMA` | No | `CORE` | Schema name |
| `SNOWFLAKE_AGENT_NAME` | No | `CLINICAL_COPILOT_AGENT` | Cortex Agent name |
| `SNOWFLAKE_WAREHOUSE` | No | `COPILOT_WH` | Warehouse for query execution |

When deployed on SPCS, `SNOWFLAKE_HOST` is set automatically by the platform and the PAT is not needed (SPCS OAuth is used instead).

---

## API Endpoints

### Members

| Method | Path | Description |
|--------|------|-------------|
| GET | `/members?q={term}` | Search members by name |
| GET | `/members/top-risk` | List members by risk flag count |
| GET | `/members/{id}` | Full member 360 detail |
| GET | `/members/{id}/summary` | Precomputed aggregates from Dynamic Table |
| GET | `/members/{id}/risk-explanation` | Why the member's risk changed |
| GET | `/risk-deltas` | Recent risk score changes |

### Agent

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ask` | Ask the Cortex Agent a clinical question (body: `{member_id, question, history}`) |

### Documents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents/upload` | Upload a document (multipart form: `file`, `member_id`, `category`) |
| GET | `/documents?category={cat}` | List documents with optional category filter |
| GET | `/documents/{id}` | Document detail with chunks |
| DELETE | `/documents/{id}` | Remove a document |

### Member Studio

| Method | Path | Description |
|--------|------|-------------|
| POST | `/studio/members` | Create a synthetic member |
| PUT | `/studio/members/{id}` | Update a member |
| POST | `/studio/members/{id}/medications` | Add a medication record |
| POST | `/studio/members/{id}/diagnoses` | Add a diagnosis record |
| POST | `/studio/members/{id}/labs` | Add a lab result |
| POST | `/studio/members/{id}/encounters` | Add an encounter |
| POST | `/studio/members/{id}/claims` | Add a claim |
| POST | `/studio/members/{id}/notes` | Add a clinical note |
| POST | `/studio/generate` | Generate a full synthetic member via AI |

### Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/users` | List application users and roles |
| GET | `/admin/users/current` | Current user info |
| POST | `/admin/users/switch-role` | Switch demo role (body: `{role}`) |
| GET | `/admin/audit?member_id=&user_role=&limit=` | AI audit log |
| GET | `/admin/jobs?limit=` | Snowflake task execution history |

---

## UI Pages

| Page | Description |
|------|-------------|
| **Worklist** | Summary KPI cards + prioritized member list by risk |
| **Members** | Search and browse all members |
| **Member Detail** | 10-tab Member 360: Overview, Chat, Timeline, Meds, Visits, Dx, Labs, Claims, Documents, Files |
| **Member Studio** | Create synthetic members manually or generate via CoCo AI |
| **Documents** | Upload, search, and manage clinical/policy/regulatory documents |
| **Jobs & Automations** | View scheduled Snowflake tasks and their execution history |
| **Audit** | Filterable AI audit log (every question, tool, latency, guardrail outcome) |
| **Settings** | User management and application info |

---

## CoCo Skills (4 reusable skills)

| Skill | File | Description |
|-------|------|-------------|
| clinical-safety-review | [`clinical-safety-review.skill.yaml`](clinical-safety-review.skill.yaml) | Safety assessment: polypharmacy, drug interactions, abnormal labs, policy compliance |
| medication-review | [`medication-review.skill.yaml`](medication-review.skill.yaml) | 6-step medication pipeline with escalation to clinical-safety-review |
| care-gap-analyzer | [`care-gap-analyzer.skill.yaml`](care-gap-analyzer.skill.yaml) | Population-level care gap coordinator with fan-out pattern |
| slack-care-alerts | [`slack-care-alerts.skill.yaml`](slack-care-alerts.skill.yaml) | MCP-powered Slack notifications for care gap alerts |

Multi-agent orchestration: `care-gap-analyzer` -> `medication-review` -> `clinical-safety-review`

---

## MCP Configuration

MCP connector config for external tool integration: [`mcp/mcp_config.json`](mcp/mcp_config.json)

| Server | Tool | Purpose |
|--------|------|---------|
| SnowCare360-slack | Slack | Post care gap alerts, risk summaries, contradiction alerts |
| SnowCare360-gdrive | Google Drive | Export compliance reports |
| SnowCare360-filesystem | Local filesystem | Save report exports to `./exports/` |

Setup: `cortex mcp add --config mcp/mcp_config.json`

---

## Data Model

15 tables + 1 Dynamic Table across 3 categories:

**Clinical**: MEMBER (50), ENCOUNTER (108), MEDICATION (99), DIAGNOSIS (108), LAB_RESULT (97), CLINICAL_NOTE (12), CLAIM (24), ATTACHMENT (18)

**Reference**: POLICY_DOCUMENT (~20), DRUG_INTERACTION_GUIDELINE (~30)

**System**: DOCUMENT, DOCUMENT_CHUNK, AI_AUDIT_LOG, APP_USER (4), RISK_DELTA_LOG (50)

**Dynamic Table**: MEMBER_360_SUMMARY (precomputed aggregates from 6 source tables)

Full schema: [docs/coco/03_data_model_and_ontology.md](docs/coco/03_data_model_and_ontology.md)

---

## Project Structure

```
snowflake-hackathon/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # App entry point, registers 5 routers
│   │   ├── config.py           # Environment variable config
│   │   ├── auth.py             # SPCS OAuth + PAT dual auth
│   │   ├── routers/            # members, agent, documents, studio, admin
│   │   ├── services/           # sql_client, snowflake_client, response_parser, audit_service, role_auth
│   │   └── models/             # Pydantic schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React + TypeScript frontend
│   ├── src/
│   │   ├── App.tsx             # Main app with page routing and member tabs
│   │   ├── components/         # 15+ components (AppNav, MemberOverview, ClinicalTimeline, etc.)
│   │   ├── styles/globals.css  # 2300+ lines of responsive styles
│   │   └── api/client.ts       # API client functions
│   ├── nginx.conf              # Reverse proxy config
│   └── Dockerfile
├── streamlit/
│   └── dashboard.py            # Streamlit-in-Snowflake population health dashboard
├── sql/                        # 10 SQL setup scripts (run in order)
├── tests/                      # 3 test suites (36 total tests)
├── docs/
│   ├── coco/                   # CoCo lifecycle evidence (9 docs)
│   │   ├── 01_planning.md
│   │   ├── 02_architecture.md
│   │   ├── 02_development.md
│   │   ├── 03_data_model_and_ontology.md
│   │   ├── 03_execution.md
│   │   ├── 04_testing.md
│   │   ├── 05_ingenuity_showcase.md
│   │   ├── 06_streamlit_and_surfaces.md
│   │   └── 07_demo_commands.md
│   ├── architecture/
│   │   └── SNOWFLAKE_RESOURCE_MAP.md
│   ├── 01_architecture.md
│   └── 05_test_results.md
├── mcp/
│   └── mcp_config.json         # MCP server config (Slack, GDrive, filesystem)
├── clinical-safety-review.skill.yaml
├── medication-review.skill.yaml
├── care-gap-analyzer.skill.yaml
├── slack-care-alerts.skill.yaml
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## CoCo Lifecycle Evidence

All planning, development, execution, and testing was done through Snowflake CoCo:

| Phase | Doc | Summary |
|-------|-----|---------|
| Planning | [01_planning.md](docs/coco/01_planning.md) | Data model design, architecture decisions, UI/UX planning |
| Architecture | [02_architecture.md](docs/coco/02_architecture.md) | Snowflake-first design, Dynamic Table rationale, Cortex Search, agent pipeline |
| Development | [02_development.md](docs/coco/02_development.md) | Code generation for backend, frontend, SQL, data |
| Data Model | [03_data_model_and_ontology.md](docs/coco/03_data_model_and_ontology.md) | 15 tables, relationships, semantic view, document pipeline |
| Execution | [03_execution.md](docs/coco/03_execution.md) | SQL execution, service config, deployment |
| Testing | [04_testing.md](docs/coco/04_testing.md) | 3 test suites, build verification |
| Ingenuity | [05_ingenuity_showcase.md](docs/coco/05_ingenuity_showcase.md) | Skills, MCP, multi-agent, automations, guardrails |
| Streamlit | [06_streamlit_and_surfaces.md](docs/coco/06_streamlit_and_surfaces.md) | Streamlit dashboard, cross-surface evidence |
| Demo | [07_demo_commands.md](docs/coco/07_demo_commands.md) | All API endpoints, sample questions, walkthrough |

---

## Test Results

| Suite | Tests | Pass Rate |
|-------|-------|-----------|
| Error Handling | 10/10 | 100% |
| New Endpoints | 22/22 | 100% |
| Guardrails | 2/4 | 50% (LLM non-determinism) |

Deterministic tests: **32/32 (100%)**. Full results: [docs/05_test_results.md](docs/05_test_results.md)

---

## SPCS Deployment (Cloud)

For deploying to Snowpark Container Services instead of local Docker:

1. Run `sql/09_deploy_spcs.sql` to create the compute pool, image repository, and service spec
2. Build and push Docker images to the Snowflake image registry
3. The service endpoint is available at the SPCS-assigned URL
4. SPCS OAuth handles authentication automatically (no PAT needed)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Lucide Icons |
| Backend | Python 3.11, FastAPI, Pydantic, httpx |
| AI | Snowflake Cortex Agent, Cortex Analyst, Cortex Search |
| Data | Snowflake (Dynamic Tables, Streams, Tasks, Stages, UDFs, Stored Procedures) |
| Deployment | Docker Compose (local), SPCS (cloud), Streamlit-in-Snowflake |
| Testing | httpx-based async test suites |

---

*Built entirely with Snowflake CoCo. All data is synthetic.*
