# CoCo Execution Evidence

## SQL Execution via CoCo

All Snowflake DDL and data operations were executed through CoCo's SQL execution capability.

### Table Creation
- Created 15 tables in CLINICAL_COPILOT.CORE schema
- Added provenance columns to POLICY_DOCUMENT (issuing_authority, jurisdiction, version)
- Created APP_USER table with 4 seeded demo users

### Snowflake Service Configuration
- Created COPILOT_WH warehouse (SMALL, Gen2)
- Created COPILOT_COMPUTE_POOL (CPU_X64_S)
- Created 3 Cortex Search services (CLINICAL_NOTES_SEARCH, POLICY_DOCS_SEARCH, DRUG_INTERACTION_SEARCH)
- Created CLINICAL_SEMANTIC_VIEW over 5 clinical tables
- Created CLINICAL_COPILOT_AGENT with claude-4-sonnet and 6 tools
- Created RISK_DELTA_NIGHTLY_TASK (CRON 0 2 * * * UTC)

### Data Pipeline
- Inserted 596 synthetic clinical records via CoCo-executed SQL
- Cortex Search services auto-indexed unstructured content
- Risk delta computation via stored procedure

### Docker / SPCS Deployment
- Built Docker images via CoCo bash tool
- Deployed to SPCS via CoCo-generated SQL
- Configured nginx reverse proxy for API routing
