-- 10_streamlit.sql: Deploy Streamlit-in-Snowflake dashboard
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;
USE WAREHOUSE COPILOT_WH;

-- Create stage for Streamlit files
CREATE STAGE IF NOT EXISTS STREAMLIT_STAGE
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Upload dashboard.py to stage (run from local machine):
-- PUT 'file:///path/to/streamlit/dashboard.py' @STREAMLIT_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Create the Streamlit app
CREATE OR REPLACE STREAMLIT SnowCare360_DASHBOARD
  ROOT_LOCATION = '@CLINICAL_COPILOT.CORE.STREAMLIT_STAGE'
  MAIN_FILE = 'dashboard.py'
  QUERY_WAREHOUSE = 'COPILOT_WH'
  TITLE = 'SnowCare360 Clinical Intelligence Dashboard'
  COMMENT = 'Population health dashboard built via CoCo showing risk distribution, medication analytics, lab trends, and AI audit activity';

-- Verify
SHOW STREAMLITS IN SCHEMA CLINICAL_COPILOT.CORE;
