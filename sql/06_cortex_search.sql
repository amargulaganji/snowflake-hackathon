-- 06_cortex_search.sql: Create 3 Cortex Search services for unstructured data
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;
USE WAREHOUSE COPILOT_WH;

-- 1. Clinical Notes Search Service
-- Enables natural-language search over clinical note text with member/type filters
CREATE OR REPLACE CORTEX SEARCH SERVICE CLINICAL_NOTES_SEARCH
  ON content_text
  ATTRIBUTES member_id, note_type, note_date
  WAREHOUSE = COPILOT_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
        note_id,
        member_id,
        encounter_id,
        note_date,
        note_type,
        author,
        content_text
    FROM CLINICAL_COPILOT.CORE.CLINICAL_NOTE
);

-- 2. Policy Documents Search Service
-- Enables search over formulary rules, prior auth criteria, coverage policies
CREATE OR REPLACE CORTEX SEARCH SERVICE POLICY_DOCS_SEARCH
  ON content_text
  ATTRIBUTES category, policy_name, topic
  WAREHOUSE = COPILOT_WH
  TARGET_LAG = '1 day'
  AS (
    SELECT
        doc_id,
        policy_name,
        category,
        source,
        topic,
        effective_date,
        content_text
    FROM CLINICAL_COPILOT.CORE.POLICY_DOCUMENT
);

-- 3. Drug Interaction Guidelines Search Service
-- Enables search over drug interaction documentation with severity filters
CREATE OR REPLACE CORTEX SEARCH SERVICE DRUG_INTERACTION_SEARCH
  ON content_text
  ATTRIBUTES drug_pair, severity
  WAREHOUSE = COPILOT_WH
  TARGET_LAG = '1 day'
  AS (
    SELECT
        guideline_id,
        drug_pair,
        severity,
        source,
        description,
        content_text
    FROM CLINICAL_COPILOT.CORE.DRUG_INTERACTION_GUIDELINE
);

-- Grant usage to roles that will access via the Cortex Agent
-- (Adjust role names as needed for your account)
-- GRANT USAGE ON CORTEX SEARCH SERVICE CLINICAL_NOTES_SEARCH TO ROLE <your_role>;
-- GRANT USAGE ON CORTEX SEARCH SERVICE POLICY_DOCS_SEARCH TO ROLE <your_role>;
-- GRANT USAGE ON CORTEX SEARCH SERVICE DRUG_INTERACTION_SEARCH TO ROLE <your_role>;
