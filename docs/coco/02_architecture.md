# Architecture Decisions

This document records the Snowflake-native architecture decisions for Sentinel360, designed and implemented through Cortex Code (CoCo).

## Snowflake-First Design

Sentinel360 runs entirely on Snowflake. No external databases, vector stores, or AI services are required.

| Concern | Snowflake Service | Alternative Avoided |
|---------|-------------------|---------------------|
| Data storage | CLINICAL_COPILOT.CORE tables | External Postgres/DynamoDB |
| AI reasoning | Cortex Agent + Cortex Analyst | OpenAI API + LangChain |
| Vector search | Cortex Search | Pinecone / Weaviate |
| File storage | Internal Stage (DOCUMENT_STAGE) | S3 / Azure Blob |
| Compute | COPILOT_WH (Gen2, SMALL) | External GPU instances |
| Deployment | SPCS (Snowpark Container Services) | AWS ECS / GKE |
| Auth | PAT + SPCS OAuth + APP_USER table | Auth0 / Cognito |

This eliminates credential sprawl, network egress, and multi-vendor debugging. Every byte of data stays inside the Snowflake security perimeter.

## Dynamic Table: MEMBER_360_SUMMARY

The member detail view requires counts from 6 tables (medications, diagnoses, labs, encounters, claims, documents) plus risk flags. Running those joins on every page load would be expensive.

**Decision**: Use a Dynamic Table with `TARGET_LAG = '1 hour'`.

```
MEMBER_360_SUMMARY precomputes per member:
  - active_medication_count
  - active_diagnosis_count
  - abnormal_lab_count
  - recent_encounter_count
  - total_claim_count
  - document_count
  - latest_encounter_date
  - risk_flag_summary
```

The member list and detail endpoints read directly from this table, avoiding multi-table joins at query time. Snowflake refreshes the materialization automatically within the target lag window.

**Trade-off**: Data can be up to 1 hour stale. This is acceptable for aggregate counts on a clinical dashboard. Real-time queries (e.g., current medications) still hit the base tables directly.

## Streams for Change Data Capture

Three streams detect incremental changes in source tables:

| Stream | Source Table | Consumer |
|--------|-------------|----------|
| DOCUMENT_CHANGE_STREAM | DOCUMENT | DOCUMENT_PROCESSING_TASK |
| MEDICATION_CHANGE_STREAM | MEDICATION | RISK_DELTA_NIGHTLY_TASK |
| LAB_RESULT_CHANGE_STREAM | LAB_RESULT | RISK_DELTA_NIGHTLY_TASK |

When a new document is uploaded, DOCUMENT_CHANGE_STREAM captures the insert. The DOCUMENT_PROCESSING_TASK reads the stream, chunks the document, and indexes chunks into the DOCUMENT_SEARCH Cortex Search service.

Medication and lab streams feed the nightly risk delta task, which recomputes polypharmacy risk only for members whose data changed -- avoiding full-table rescans.

## Cortex Search Services

Four Cortex Search services provide hybrid vector + keyword retrieval:

| Service | Source | Search Column | Attributes | Use Case |
|---------|--------|---------------|------------|----------|
| CLINICAL_NOTES_SEARCH | CLINICAL_NOTE | NOTE_TEXT | MEMBER_ID, PROVIDER_NAME, NOTE_DATE | Find relevant clinical notes for a member |
| POLICY_DOCS_SEARCH | POLICY_DOCUMENT | POLICY_TEXT | POLICY_TYPE, EFFECTIVE_DATE | Retrieve policy rules for compliance checks |
| DRUG_INTERACTION_SEARCH | DRUG_INTERACTION_GUIDELINE | GUIDELINE_TEXT | DRUG_PAIR, SEVERITY | Look up known drug interactions |
| DOCUMENT_SEARCH | DOCUMENT_CHUNK | CHUNK_TEXT | DOCUMENT_ID, CATEGORY, MEMBER_ID | Search uploaded documents |

Each service is configured with `TARGET_LAG = '1 hour'` to stay current with source table changes. The Cortex Agent selects which services to query based on the user's question.

## Cortex Agent: 7-Tool Agentic RAG

The CLINICAL_COPILOT_AGENT orchestrates 7 tools in a 3-stage pipeline:

**Stage 1 -- Retrieval**
1. **Cortex Analyst** (NL-to-SQL via CLINICAL_SEMANTIC_VIEW) -- structured clinical data
2. **Clinical Notes Search** -- unstructured clinical notes
3. **Policy Docs Search** -- health plan policy documents
4. **Drug Interaction Search** -- drug interaction guidelines
5. **Document Search** -- user-uploaded documents

**Stage 2 -- Risk Assessment**
6. **SCORE_POLYPHARMACY_RISK** (UDF) -- deterministic polypharmacy risk scoring

**Stage 3 -- Compliance**
7. **CHECK_POLICY_COMPLIANCE** (UDF) -- deterministic policy compliance check

The agent decides which tools to invoke per question. A medication question may use tools 1, 2, 4, and 6. A policy question may use tools 1, 3, and 7. Every response includes which stages contributed, enabling auditability.

## Internal Stage: DOCUMENT_STAGE

Documents uploaded through the UI are stored on DOCUMENT_STAGE, an internal stage with SNOWFLAKE_SSE encryption. The upload flow:

1. User uploads file via `POST /documents/upload`
2. Backend PUTs file to `@DOCUMENT_STAGE/{member_id}/{filename}`
3. Metadata row inserted into DOCUMENT table
4. DOCUMENT_CHANGE_STREAM captures the insert
5. DOCUMENT_PROCESSING_TASK chunks the file and writes to DOCUMENT_CHUNK
6. DOCUMENT_SEARCH Cortex Search service indexes the chunks

No files leave Snowflake. The stage acts as a secure, governed file system.

## Deployment: FastAPI + React on SPCS

The application runs as two containers in a single SPCS service:

| Container | Framework | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI (Python) | REST API, Snowflake SQL Statement API calls, Cortex Agent invocation |
| Frontend | React (TypeScript) | Member dashboard, agent chat, document upload, admin panel |

Both containers are built as Docker images, pushed to the COPILOT_IMAGES repository, and deployed to COPILOT_COMPUTE_POOL (CPU_X64_S). SPCS provides Snowflake-native OAuth for service-to-Snowflake authentication.

## Role-Based Access

The APP_USER table stores application-level roles:

| Role | Capabilities |
|------|-------------|
| clinician | View members, ask clinical questions, upload documents |
| admin | All clinician capabilities + user management, audit log access, job management |
| readonly | View members and summaries only, no agent or upload access |

Role switching is exposed via `POST /admin/users/switch-role`. The backend checks the user's role on every request and filters available endpoints accordingly.

## Dual Data Path

Sentinel360 uses two data paths optimized for different latency requirements:

- **Direct SQL (SQL Statement API)**: Member search, detail, top-risk, and summary endpoints execute parameterized SQL for sub-second responses. No LLM involved.
- **Cortex Agent**: The `/ask` endpoint routes through the full 3-stage pipeline. Response times are 10-30 seconds but include reasoning, evidence chains, and citations.

This separation keeps the UI responsive for navigation while reserving the AI pipeline for analytical questions.
