# CoCo Planning Evidence

## Architecture Decisions

All planning for Sentinel360 was done through Snowflake CoCo (Cortex Code), the Snowflake-native AI development assistant.

### Data Model Design
- Designed 11-table clinical data model through CoCo conversation
- Tables: MEMBER, ENCOUNTER, MEDICATION, DIAGNOSIS, LAB_RESULT, CLINICAL_NOTE, POLICY_DOCUMENT, DRUG_INTERACTION_GUIDELINE, CLAIM, ATTACHMENT, RISK_DELTA_LOG
- Added DOCUMENT, DOCUMENT_CHUNK, AI_AUDIT_LOG, APP_USER tables in upgrade phase
- All referential integrity maintained (MEMBER_ID as FK across all clinical tables)

### Architecture Design
- 3-Stage AI Pipeline: Retrieval -> Risk Assessment -> Compliance
- Cortex Agent with 6 tools (Cortex Analyst + 3 Cortex Search + 2 UDFs)
- Dual data path: Direct SQL for member search/detail (<1s), Cortex Agent for AI Q&A
- SPCS deployment architecture with OAuth + PAT dual auth

### UI/UX Planning
- Phased implementation plan: 8 phases from data model to cleanup
- Navigation restructure: sidebar-only -> persistent left nav with role-based sections
- Member 360 with 10 tabs (Overview, Chat, Timeline, Meds, Visits, Dx, Labs, Claims, Documents, Files)
- Lane-based timeline redesign with zoom, scroll, and event detail drawer

### Feature Planning
- Identified 15+ gaps between current state and hackathon requirements
- Prioritized: document ingestion, inline citations, member studio, roles/audit
- Planned parallel implementation using CoCo team workflow
