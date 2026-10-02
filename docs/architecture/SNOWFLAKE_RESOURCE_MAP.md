# Snowflake Resource Map

Comprehensive inventory of every Snowflake object used by Sentinel360.

**Account**: MQBQAAP-MH56160
**Database**: CLINICAL_COPILOT
**Schema**: CORE
**Warehouse**: COPILOT_WH
**User**: AMARGULAGANJI

## Warehouse

| Property | Value |
|----------|-------|
| Name | COPILOT_WH |
| Size | SMALL |
| Type | Gen2 |
| Auto-suspend | 60 seconds |
| Auto-resume | Yes |
| Purpose | All query execution, Dynamic Table refresh, Task execution |

## Tables (15)

### Core Clinical Tables

| Table | PK | Row Count | Description |
|-------|----|-----------|-------------|
| MEMBER | MEMBER_ID | 50 | Patient demographics, plan type, PCP, risk flags |
| ENCOUNTER | ENCOUNTER_ID | 108 | Clinical visits with type, date, provider, notes |
| MEDICATION | MEDICATION_ID | 99 | Prescriptions: drug name, dosage, frequency, status |
| DIAGNOSIS | DIAGNOSIS_ID | 108 | ICD-10 diagnoses with status and date |
| LAB_RESULT | LAB_ID | 97 | Lab values with reference ranges, abnormal flags |
| CLINICAL_NOTE | NOTE_ID | 12 | Free-text clinical notes by provider |
| CLAIM | CLAIM_ID | 24 | Insurance claims: amounts, status, denial reasons |
| ATTACHMENT | ATTACHMENT_ID | 18 | Document metadata linked to encounters |

### Reference Tables

| Table | PK | Row Count | Description |
|-------|----|-----------|-------------|
| POLICY_DOCUMENT | POLICY_ID | ~20 | Health plan policy docs for compliance checking |
| DRUG_INTERACTION_GUIDELINE | GUIDELINE_ID | ~30 | Drug interaction guidelines for risk scoring |

### System Tables

| Table | PK | Row Count | Description |
|-------|----|-----------|-------------|
| DOCUMENT | DOCUMENT_ID | varies | Uploaded document metadata |
| DOCUMENT_CHUNK | CHUNK_ID | varies | Chunked document content for search indexing |
| AI_AUDIT_LOG | LOG_ID | grows | Agent question/response audit trail |
| APP_USER | USER_ID | ~5 | Application users and roles |
| RISK_DELTA_LOG | DELTA_ID | grows | Historical risk score changes |

## Dynamic Table (1)

| Property | Value |
|----------|-------|
| Name | MEMBER_360_SUMMARY |
| Target Lag | 1 hour |
| Warehouse | COPILOT_WH |
| Source Tables | MEMBER, ENCOUNTER, MEDICATION, DIAGNOSIS, LAB_RESULT, CLAIM, DOCUMENT |
| Purpose | Precomputed per-member aggregates for dashboard performance |

## Semantic View (1)

| Property | Value |
|----------|-------|
| Name | CLINICAL_SEMANTIC_VIEW |
| Type | Semantic |
| Used By | Cortex Analyst (via Cortex Agent) |
| Verified Queries | 8 |
| Purpose | NL-to-SQL ontology for clinical data queries |

## Streams (3)

| Stream | Source Table | Type | Purpose |
|--------|-------------|------|---------|
| DOCUMENT_CHANGE_STREAM | DOCUMENT | Append-only | Triggers document chunking/indexing |
| MEDICATION_CHANGE_STREAM | MEDICATION | Append-only | Triggers risk delta recomputation |
| LAB_RESULT_CHANGE_STREAM | LAB_RESULT | Append-only | Triggers risk delta recomputation |

## Stage (1)

| Property | Value |
|----------|-------|
| Name | DOCUMENT_STAGE |
| Type | Internal |
| Encryption | SNOWFLAKE_SSE |
| Purpose | Uploaded document file storage |

## Cortex Search Services (4)

| Service | Source Table | Search Column | Key Attributes | Target Lag |
|---------|-------------|---------------|----------------|------------|
| CLINICAL_NOTES_SEARCH | CLINICAL_NOTE | NOTE_TEXT | MEMBER_ID, PROVIDER_NAME, NOTE_DATE | 1 hour |
| POLICY_DOCS_SEARCH | POLICY_DOCUMENT | POLICY_TEXT | POLICY_TYPE, EFFECTIVE_DATE | 1 hour |
| DRUG_INTERACTION_SEARCH | DRUG_INTERACTION_GUIDELINE | GUIDELINE_TEXT | DRUG_PAIR, SEVERITY | 1 hour |
| DOCUMENT_SEARCH | DOCUMENT_CHUNK | CHUNK_TEXT | DOCUMENT_ID, CATEGORY, MEMBER_ID | 1 hour |

## UDFs (2)

| UDF | Return Type | Purpose |
|-----|-------------|---------|
| SCORE_POLYPHARMACY_RISK | VARIANT | Deterministic polypharmacy risk scoring with flagged drug pairs and reasoning |
| CHECK_POLICY_COMPLIANCE | VARIANT | Deterministic policy compliance check with gaps and cited policies |

## Cortex Agent (1)

| Property | Value |
|----------|-------|
| Name | CLINICAL_COPILOT_AGENT |
| Tools | 7 (Cortex Analyst, 4 Cortex Search, 2 UDFs) |
| Semantic View | CLINICAL_SEMANTIC_VIEW |
| Purpose | Multi-tool agentic RAG for clinical queries |

## Tasks (2)

| Task | Schedule | Purpose |
|------|----------|---------|
| RISK_DELTA_NIGHTLY_TASK | Daily | Recomputes risk deltas for members with changed medications/labs |
| DOCUMENT_PROCESSING_TASK | Stream-triggered | Chunks new documents and writes to DOCUMENT_CHUNK |

## Stored Procedure (1)

| Property | Value |
|----------|-------|
| Name | REFRESH_RISK_DELTAS |
| Called By | RISK_DELTA_NIGHTLY_TASK |
| Purpose | Computes risk score changes, writes to RISK_DELTA_LOG |

## Compute Pool (1)

| Property | Value |
|----------|-------|
| Name | COPILOT_COMPUTE_POOL |
| Instance Family | CPU_X64_S |
| Purpose | SPCS container execution |

## SPCS Service (1)

| Property | Value |
|----------|-------|
| Name | COPILOT_SERVICE |
| Compute Pool | COPILOT_COMPUTE_POOL |
| Containers | FastAPI backend + React frontend |
| Auth | SPCS OAuth |

## Image Repository (1)

| Property | Value |
|----------|-------|
| Name | COPILOT_IMAGES |
| Database | CLINICAL_COPILOT |
| Schema | CORE |
| Purpose | Docker image storage for SPCS deployment |

## Object Count Summary

| Category | Count |
|----------|-------|
| Tables | 15 |
| Dynamic Tables | 1 |
| Semantic Views | 1 |
| Streams | 3 |
| Stages | 1 |
| Cortex Search Services | 4 |
| UDFs | 2 |
| Cortex Agents | 1 |
| Tasks | 2 |
| Stored Procedures | 1 |
| Compute Pools | 1 |
| SPCS Services | 1 |
| Image Repositories | 1 |
| **Total Objects** | **34** |
