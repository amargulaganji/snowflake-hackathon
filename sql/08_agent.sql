-- 08_agent.sql: Create the Cortex Agent with all 7 tools and guardrails
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;
USE WAREHOUSE COPILOT_WH;

CREATE OR REPLACE AGENT CLINICAL_COPILOT.CORE.CLINICAL_COPILOT_AGENT
  COMMENT = 'Clinical compliance copilot with 7 tools including document search'
  FROM SPECIFICATION
$$
models:
  orchestration: "auto"
instructions:
  response: "You are a clinical compliance copilot. GUARDRAILS: 1) Evidence-grounded only. 2) Include reasoning trace. 3) Decline when uncertain. 4) Detect contradictions. 5) Use numbered citations [1][2][3]. Include Risk Level for medication queries."
  orchestration: "For clinical queries: clinical_analyst first, then clinical_notes_search and document_search for corroboration, then drug_interaction_search. For policy: policy_docs_search first. For risk: score_polypharmacy_risk then clinical_analyst. Always cross-validate with multiple tools."
  sample_questions:
    - question: "What medications is Eleanor Vance currently taking?"
    - question: "What is the polypharmacy risk for member M010?"
    - question: "Show drug interactions for member M002"
    - question: "What changed after the latest hospitalization?"
    - question: "Which members have the highest polypharmacy risk?"
tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "clinical_analyst"
      description: "Query structured clinical data via semantic view."
  - tool_spec:
      type: "cortex_search"
      name: "clinical_notes_search"
      description: "Search clinical notes for context and corroboration."
  - tool_spec:
      type: "cortex_search"
      name: "policy_docs_search"
      description: "Search policy documents for compliance rules."
  - tool_spec:
      type: "cortex_search"
      name: "drug_interaction_search"
      description: "Search drug interaction guidelines."
  - tool_spec:
      type: "cortex_search"
      name: "document_search"
      description: "Search uploaded clinical and regulatory documents for evidence."
  - tool_spec:
      type: "generic"
      name: "score_polypharmacy_risk"
      description: "Calculate polypharmacy risk score."
      input_schema:
        type: "object"
        properties:
          member_id:
            type: "string"
            description: "Member ID"
        required:
          - "member_id"
  - tool_spec:
      type: "generic"
      name: "check_policy_compliance"
      description: "Check medication policy compliance."
      input_schema:
        type: "object"
        properties:
          member_id:
            type: "string"
            description: "Member ID"
          drug_name:
            type: "string"
            description: "Drug name"
        required:
          - "member_id"
          - "drug_name"
tool_resources:
  clinical_analyst:
    semantic_view: "CLINICAL_COPILOT.CORE.CLINICAL_SEMANTIC_VIEW"
    execution_environment:
      type: "warehouse"
      warehouse: "COPILOT_WH"
  clinical_notes_search:
    search_service: "CLINICAL_COPILOT.CORE.CLINICAL_NOTES_SEARCH"
    max_results: 10
  policy_docs_search:
    search_service: "CLINICAL_COPILOT.CORE.POLICY_DOCS_SEARCH"
    max_results: 5
  drug_interaction_search:
    search_service: "CLINICAL_COPILOT.CORE.DRUG_INTERACTION_SEARCH"
    max_results: 10
  document_search:
    search_service: "CLINICAL_COPILOT.CORE.DOCUMENT_SEARCH"
    max_results: 10
  score_polypharmacy_risk:
    type: "function"
    execution_environment:
      type: "warehouse"
      warehouse: "COPILOT_WH"
    identifier: "CLINICAL_COPILOT.CORE.SCORE_POLYPHARMACY_RISK"
  check_policy_compliance:
    type: "function"
    execution_environment:
      type: "warehouse"
      warehouse: "COPILOT_WH"
    identifier: "CLINICAL_COPILOT.CORE.CHECK_POLICY_COMPLIANCE"
$$;

-- Verify the agent was created
SHOW AGENTS IN SCHEMA CLINICAL_COPILOT.CORE;
DESCRIBE AGENT CLINICAL_COPILOT.CORE.CLINICAL_COPILOT_AGENT;
