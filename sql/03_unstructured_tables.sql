-- 03_unstructured_tables.sql: Unstructured / document tables
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;

CREATE OR REPLACE TABLE CLINICAL_NOTE (
    note_id       VARCHAR PRIMARY KEY,
    member_id     VARCHAR,
    encounter_id  VARCHAR,
    note_date     DATE,
    note_type     VARCHAR,  -- progress/discharge/consult/referral
    author        VARCHAR,
    content_text  VARCHAR
);

CREATE OR REPLACE TABLE POLICY_DOCUMENT (
    doc_id          VARCHAR PRIMARY KEY,
    policy_name     VARCHAR,
    category        VARCHAR,  -- formulary/prior-auth/step-therapy/coverage
    source          VARCHAR,
    topic           VARCHAR,
    effective_date  DATE,
    content_text    VARCHAR
);

CREATE OR REPLACE TABLE DRUG_INTERACTION_GUIDELINE (
    guideline_id  VARCHAR PRIMARY KEY,
    drug_pair     VARCHAR,  -- "DrugA + DrugB"
    severity      VARCHAR,  -- minor/moderate/major/contraindicated
    source        VARCHAR,
    description   VARCHAR,
    content_text  VARCHAR
);
