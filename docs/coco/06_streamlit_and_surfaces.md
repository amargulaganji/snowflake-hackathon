# CoCo Streamlit & Cross-Surface Evidence

## Streamlit-in-Snowflake Dashboard

**Object**: CLINICAL_COPILOT.CORE.SnowCare360_DASHBOARD
**File**: `streamlit/dashboard.py`
**SQL**: `sql/10_streamlit.sql`
**Warehouse**: COPILOT_WH
**Stage**: @STREAMLIT_STAGE

### Dashboard Sections

The Streamlit dashboard provides a read-only population health analytics view, complementing the interactive SPCS app.

| Section | Data Source | Visualization |
|---------|-----------|---------------|
| KPI Row | MEMBER, MEDICATION, LAB_RESULT, AI_AUDIT_LOG | 5 metric cards: Total Members, High Risk, Active Medications, Abnormal Labs, AI Queries |
| Risk Distribution | MEMBER (ARRAY_SIZE of RISK_FLAGS) | Bar chart: High/Moderate/Low |
| Plan Distribution | MEMBER (PLAN_TYPE) | Bar chart by plan type |
| Top 10 Medications | MEDICATION (active, grouped by DRUG_NAME) | Bar chart |
| Abnormal Labs | LAB_RESULT (ABNORMAL_FLAG = TRUE, grouped by TEST_NAME) | Bar chart |
| Encounters by Type | ENCOUNTER (grouped by ENCOUNTER_TYPE) | Bar chart |
| Medication Status | MEDICATION (grouped by STATUS) | Bar chart |
| Member Risk Table | MEMBER JOIN MEMBER_360_SUMMARY | Sortable dataframe |
| AI Audit Log | AI_AUDIT_LOG | Dataframe with tools, latency, guardrail flags |
| Task History | INFORMATION_SCHEMA.TASK_HISTORY | Recent task executions |

### How It Was Built

1. CoCo generated the dashboard.py with Snowpark session queries
2. CoCo executed PUT to upload to @STREAMLIT_STAGE
3. CoCo executed CREATE STREAMLIT DDL
4. Dashboard is accessible in Snowsight under Streamlit Apps

### Cross-Surface Summary

| Surface | Component | Access |
|---------|-----------|--------|
| SPCS App (React) | Full interactive app: member search, agent chat, document upload, admin panel | https://abr2gc-mqbqaap-mh56160.snowflakecomputing.app |
| Streamlit-in-Snowflake | Read-only analytics dashboard with charts and KPIs | Snowsight > Streamlit Apps > SnowCare360_DASHBOARD |
| Cortex Agent in Snowsight | Direct agent queries via Snowsight "Ask Cortex" | Snowsight > Cortex Agent > CLINICAL_COPILOT_AGENT |
| CoCo Desktop | Development, testing, skill execution, automation | Local CLI sessions |
| CoCo Skills | Reusable clinical-safety-review, medication-review, care-gap-analyzer | Any CoCo session |
