-- 09_deploy_spcs.sql: Deploy Clinical Copilot to Snowpark Container Services
-- Run AFTER building and pushing Docker images to the Snowflake registry.
--
-- Prerequisites:
--   1. Docker images pushed to:
--      mqbqaap-mh56160.registry.snowflakecomputing.com/clinical_copilot/core/copilot_images/backend:latest
--      mqbqaap-mh56160.registry.snowflakecomputing.com/clinical_copilot/core/copilot_images/frontend:latest
--   2. All Snowflake objects from sql/01-08 already created.

USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;
USE WAREHOUSE COPILOT_WH;

-- Step 1: Image repository (already created, but idempotent)
CREATE IMAGE REPOSITORY IF NOT EXISTS CLINICAL_COPILOT.CORE.COPILOT_IMAGES;

-- Step 2: Create a dedicated compute pool (system pools don't support generic services)
CREATE COMPUTE POOL IF NOT EXISTS COPILOT_COMPUTE_POOL
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_S
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 300;

-- Step 3: Grant necessary privileges
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE ACCOUNTADMIN;

-- Step 4: Create the service with two containers (backend + frontend)
CREATE SERVICE CLINICAL_COPILOT.CORE.COPILOT_SERVICE
  IN COMPUTE POOL COPILOT_COMPUTE_POOL
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1
  FROM SPECIFICATION $$
spec:
  containers:
    - name: backend
      image: /clinical_copilot/core/copilot_images/backend:latest
      env:
        SNOWFLAKE_DATABASE: CLINICAL_COPILOT
        SNOWFLAKE_SCHEMA: CORE
        SNOWFLAKE_AGENT_NAME: CLINICAL_COPILOT_AGENT
        SNOWFLAKE_WAREHOUSE: COPILOT_WH
      readinessProbe:
        port: 8000
        path: /health
      resources:
        requests:
          cpu: 0.5
          memory: 512M
        limits:
          cpu: 1
          memory: 1G

    - name: frontend
      image: /clinical_copilot/core/copilot_images/frontend:latest
      readinessProbe:
        port: 80
        path: /
      resources:
        requests:
          cpu: 0.25
          memory: 256M
        limits:
          cpu: 0.5
          memory: 512M

  endpoints:
    - name: app
      port: 80
      public: true
$$;

-- Step 4: Check service status
SHOW SERVICES IN SCHEMA CLINICAL_COPILOT.CORE;
DESCRIBE SERVICE CLINICAL_COPILOT.CORE.COPILOT_SERVICE;

-- Step 5: Get the public endpoint URL (use this to access the app)
SHOW ENDPOINTS IN SERVICE CLINICAL_COPILOT.CORE.COPILOT_SERVICE;

-- Step 6: View service logs (for debugging)
-- SELECT SYSTEM$GET_SERVICE_LOGS('CLINICAL_COPILOT.CORE.COPILOT_SERVICE', '0', 'backend', 50);
-- SELECT SYSTEM$GET_SERVICE_LOGS('CLINICAL_COPILOT.CORE.COPILOT_SERVICE', '0', 'frontend', 50);

-- To suspend/resume/drop the service:
-- ALTER SERVICE CLINICAL_COPILOT.CORE.COPILOT_SERVICE SUSPEND;
-- ALTER SERVICE CLINICAL_COPILOT.CORE.COPILOT_SERVICE RESUME;
-- DROP SERVICE CLINICAL_COPILOT.CORE.COPILOT_SERVICE;
