-- 05_create_semantic_view.sql: Create semantic view from YAML
-- Run after 02_structured_tables.sql and 04_synthetic_data.sql
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;
USE WAREHOUSE COPILOT_WH;

-- Create the semantic view from the YAML file
-- First, upload the YAML to a stage
CREATE STAGE IF NOT EXISTS CLINICAL_COPILOT.CORE.SEMANTIC_STAGE;

-- Upload the YAML file to the stage (run from SnowSQL or Snowsight):
-- PUT file://sql/05_semantic_view.yaml @CLINICAL_COPILOT.CORE.SEMANTIC_STAGE AUTO_COMPRESS=FALSE;

-- Then create the semantic view
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
  'CLINICAL_COPILOT.CORE.CLINICAL_SEMANTIC_VIEW',
  '@CLINICAL_COPILOT.CORE.SEMANTIC_STAGE/05_semantic_view.yaml'
);

-- Verify the semantic view was created
DESCRIBE SEMANTIC VIEW CLINICAL_COPILOT.CORE.CLINICAL_SEMANTIC_VIEW;
