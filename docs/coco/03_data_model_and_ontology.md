# Data Model & Ontology

This document describes the Sentinel360 data model: 15 tables, 1 Dynamic Table, 3 streams, 4 Cortex Search services, and the semantic view ontology.

## Entity-Relationship Overview

**MEMBER** is the central entity. All clinical tables reference it via `MEMBER_ID` as a foreign key.

```
                              +----------------+
                              |    MEMBER      |
                              |   (50 rows)    |
                              +-------+--------+
        +----------+----------+-------+-------+----------+----------+
        |          |          |               |          |          |
   ENCOUNTER  MEDICATION  DIAGNOSIS     LAB_RESULT   CLAIM   CLINICAL_NOTE
    (108)       (99)       (108)          (97)       (24)       (12)
        |
    ATTACHMENT (18)
```

Reference tables (POLICY_DOCUMENT, DRUG_INTERACTION_GUIDELINE) are not keyed to MEMBER_ID. They serve as knowledge bases for the Cortex Agent tools.

System tables (DOCUMENT, DOCUMENT_CHUNK, AI_AUDIT_LOG, APP_USER, RISK_DELTA_LOG) support application operations.

## Table Inventory (15 Tables)

### Core Clinical Tables

| Table | PK | FK | Row Count | Purpose |
|-------|----|----|-----------|---------|
| MEMBER | MEMBER_ID | -- | 50 | Demographics, plan type, PCP, risk flags |
| ENCOUNTER | ENCOUNTER_ID | MEMBER_ID | 108 | Clinical visits: type, date, provider, notes |
| MEDICATION | MEDICATION_ID | MEMBER_ID | 99 | Prescriptions: drug name, dosage, frequency, status |
| DIAGNOSIS | DIAGNOSIS_ID | MEMBER_ID | 108 | ICD-10 codes with status and date |
| LAB_RESULT | LAB_ID | MEMBER_ID | 97 | Lab values with reference ranges, abnormal flags |
| CLINICAL_NOTE | NOTE_ID | MEMBER_ID | 12 | Free-text clinical notes by provider |
| CLAIM | CLAIM_ID | MEMBER_ID | 24 | Insurance claims: amounts, status, denial reasons |
| ATTACHMENT | ATTACHMENT_ID | ENCOUNTER_ID | 18 | Document metadata linked to encounters |

### Reference Tables

| Table | PK | Row Count | Purpose |
|-------|----|-----------|---------|
| POLICY_DOCUMENT | POLICY_ID | ~20 | Health plan policy documents for compliance checking |
| DRUG_INTERACTION_GUIDELINE | GUIDELINE_ID | ~30 | Drug interaction guidelines for risk scoring |

POLICY_DOCUMENT includes provenance columns:
- `SOURCE` -- origin of the policy (e.g., CMS, internal compliance)
- `EFFECTIVE_DATE` / `EXPIRATION_DATE` -- validity window
- `VERSION` -- document version for audit trail
- `LAST_REVIEWED_BY` -- reviewer identifier

### System Tables

| Table | PK | Row Count | Purpose |
|-------|----|-----------|---------|
| DOCUMENT | DOCUMENT_ID | varies | Uploaded document metadata: category, upload date, member link |
| DOCUMENT_CHUNK | CHUNK_ID | varies | Chunked content for Cortex Search indexing |
| AI_AUDIT_LOG | LOG_ID | grows | Audit trail: every agent question, response, tools invoked |
| APP_USER | USER_ID | ~5 | Application users with roles and permissions |
| RISK_DELTA_LOG | DELTA_ID | grows | Historical risk score changes with contributing factors |

## Dynamic Table: MEMBER_360_SUMMARY

Precomputes per-member aggregates to avoid expensive joins on every page load.

| Column | Source | Description |
|--------|--------|-------------|
| MEMBER_ID | MEMBER | Primary key |
| ACTIVE_MEDICATION_COUNT | MEDICATION | WHERE STATUS = 'active' |
| ACTIVE_DIAGNOSIS_COUNT | DIAGNOSIS | WHERE STATUS = 'active' |
| ABNORMAL_LAB_COUNT | LAB_RESULT | WHERE ABNORMAL_FLAG = TRUE |
| RECENT_ENCOUNTER_COUNT | ENCOUNTER | Last 12 months |
| TOTAL_CLAIM_COUNT | CLAIM | All claims |
| DOCUMENT_COUNT | DOCUMENT | Uploaded documents |
| LATEST_ENCOUNTER_DATE | ENCOUNTER | MAX(ENCOUNTER_DATE) |
| RISK_FLAG_SUMMARY | MEMBER | Aggregated risk flags |

Configuration: `TARGET_LAG = '1 hour'`, warehouse COPILOT_WH.

## Key Relationships

```
MEMBER.MEMBER_ID  --->  ENCOUNTER.MEMBER_ID
                  --->  MEDICATION.MEMBER_ID
                  --->  DIAGNOSIS.MEMBER_ID
                  --->  LAB_RESULT.MEMBER_ID
                  --->  CLINICAL_NOTE.MEMBER_ID
                  --->  CLAIM.MEMBER_ID
                  --->  DOCUMENT.MEMBER_ID

ENCOUNTER.ENCOUNTER_ID  --->  ATTACHMENT.ENCOUNTER_ID
```

All foreign keys use MEMBER_ID as the join column. There is no cross-table join between clinical tables except through MEMBER.

## Streams (3)

| Stream | Source Table | Purpose |
|--------|-------------|---------|
| DOCUMENT_CHANGE_STREAM | DOCUMENT | Triggers document chunking and search indexing |
| MEDICATION_CHANGE_STREAM | MEDICATION | Triggers risk delta recomputation for affected members |
| LAB_RESULT_CHANGE_STREAM | LAB_RESULT | Triggers risk delta recomputation for affected members |

Streams are append-only. They feed scheduled Tasks that process only the changed rows.

## Semantic View: CLINICAL_SEMANTIC_VIEW

Provides the NL-to-SQL interface for Cortex Analyst. The semantic view defines:

### Dimensions
- Member demographics: ID, name, age, gender, plan type
- Encounter details: type, date, provider
- Medication attributes: drug name, dosage, frequency, status
- Diagnosis attributes: ICD-10 code, description, status
- Lab attributes: test name, result value, reference range

### Facts and Metrics
- Medication counts (active, total)
- Diagnosis counts (active, total)
- Lab result aggregates (abnormal count, latest values)
- Encounter frequency and recency
- Claim amounts and denial rates

### Verified Queries (8)
Pre-validated query patterns that ensure Cortex Analyst generates correct SQL:
- Active medications for a member
- Abnormal lab results
- Recent encounters
- Polypharmacy risk indicators
- Diagnosis history
- Claim denial analysis
- Member demographic summary
- Provider encounter frequency

## Document Ingestion Pipeline

The document pipeline flows through three stages:

```
User Upload
    |
    v
DOCUMENT table          (metadata: filename, category, member_id, upload_date)
    |
    v
DOCUMENT_CHANGE_STREAM  (CDC captures new inserts)
    |
    v
DOCUMENT_PROCESSING_TASK (chunks document into segments)
    |
    v
DOCUMENT_CHUNK table    (chunk_text, chunk_index, document_id)
    |
    v
DOCUMENT_SEARCH         (Cortex Search service indexes chunks)
```

Files are stored on DOCUMENT_STAGE (internal, SNOWFLAKE_SSE encryption). The chunking task splits documents into overlapping segments suitable for semantic search. The DOCUMENT_SEARCH Cortex Search service refreshes within its target lag to make new chunks queryable.
