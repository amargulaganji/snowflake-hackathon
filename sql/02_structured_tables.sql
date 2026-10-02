-- 02_structured_tables.sql: Core structured tables
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;

CREATE OR REPLACE TABLE MEMBER (
    member_id       VARCHAR PRIMARY KEY,
    first_name      VARCHAR,
    last_name       VARCHAR,
    dob             DATE,
    age             INT,
    gender          VARCHAR,
    plan_type       VARCHAR,
    enrollment_date DATE,
    pcp_name        VARCHAR,
    risk_flags      VARIANT  -- array of strings
);

CREATE OR REPLACE TABLE ENCOUNTER (
    encounter_id           VARCHAR PRIMARY KEY,
    member_id              VARCHAR REFERENCES MEMBER(member_id),
    encounter_date         DATE,
    encounter_type         VARCHAR,  -- inpatient/outpatient/ER/telehealth
    provider_name          VARCHAR,
    facility               VARCHAR,
    primary_diagnosis_code VARCHAR,
    notes_summary          VARCHAR,
    notes_doc_id           VARCHAR
);

CREATE OR REPLACE TABLE MEDICATION (
    medication_id VARCHAR PRIMARY KEY,
    member_id     VARCHAR REFERENCES MEMBER(member_id),
    drug_name     VARCHAR,
    ndc_code      VARCHAR,
    dosage        VARCHAR,
    route         VARCHAR,
    frequency     VARCHAR,
    start_date    DATE,
    end_date      DATE,
    prescriber    VARCHAR,
    status        VARCHAR  -- active/discontinued/on-hold
);

CREATE OR REPLACE TABLE DIAGNOSIS (
    diagnosis_id       VARCHAR PRIMARY KEY,
    member_id          VARCHAR REFERENCES MEMBER(member_id),
    icd10_code         VARCHAR,
    description        VARCHAR,
    diagnosed_date     DATE,
    status             VARCHAR,  -- active/resolved/chronic
    diagnosing_provider VARCHAR
);

CREATE OR REPLACE TABLE LAB_RESULT (
    lab_id              VARCHAR PRIMARY KEY,
    member_id           VARCHAR REFERENCES MEMBER(member_id),
    test_name           VARCHAR,
    loinc_code          VARCHAR,
    result_value        FLOAT,
    unit                VARCHAR,
    reference_range_low  FLOAT,
    reference_range_high FLOAT,
    result_date         DATE,
    abnormal_flag       BOOLEAN
);
