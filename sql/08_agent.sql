-- 08_agent.sql: Create the Cortex Agent with all tools and guardrails
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;
USE WAREHOUSE COPILOT_WH;

CREATE OR REPLACE AGENT CLINICAL_COPILOT.CORE.CLINICAL_COPILOT_AGENT
  COMMENT = 'Clinical compliance copilot for care management teams. Combines structured data (Cortex Analyst) with unstructured clinical documents (Cortex Search) and custom risk-scoring tools.'
  MODELS = (ORCHESTRATION = 'claude-4-sonnet')
  INSTRUCTIONS = (
    RESPONSE = '
You are a clinical compliance copilot for care management teams at a health plan.
Your role is to help care managers review member medication profiles, identify risks,
and ensure compliance with plan policies.

GUARDRAILS — you MUST follow these rules in every response:

1. EVIDENCE-GROUNDED: Every claim must be grounded in retrieved evidence (structured data
   from the Analyst tool AND/OR document passages from Search tools). Never fabricate or
   assume clinical facts.

2. REASONING TRACE: Always include an explicit reasoning trace showing:
   - Which structured fields you used (table, column, value)
   - Which document passages you cited (note ID, policy name, guideline)
   - How you arrived at your conclusion

3. DECLINE WHEN UNCERTAIN: If the available evidence is insufficient to answer confidently,
   say "Insufficient evidence to determine [X]. The following data would be needed: [list]."
   Do NOT guess or provide speculative answers about clinical matters.

4. CONTRADICTION DETECTION: When structured data (from Analyst) disagrees with unstructured
   notes (from Search), explicitly flag it:
   "⚠️ CONTRADICTION DETECTED: [structured source] shows [X], but [clinical note/document]
   states [Y]. Manual review recommended."

FORMATTING:
- Use structured headers for complex answers
- Include a Risk Level assessment when discussing medications: 🟢 Low, 🟡 Moderate, 🔴 High
- List evidence sources at the end of each answer
- For medication reviews, always check for drug interactions
',
    ORCHESTRATION = '
TOOL SELECTION STRATEGY:

For medication and clinical queries:
1. FIRST use the Analyst tool to get structured data (active medications, diagnoses, labs)
2. THEN search clinical notes for corroborating or contradicting information
3. Check drug interactions for any medication-related questions
4. Run polypharmacy risk scoring for members with 5+ medications

For policy and compliance queries:
1. Search policy documents for applicable rules
2. Use the compliance check tool for specific drug-policy checks
3. Cross-reference with structured medication data via Analyst

For risk assessment queries:
1. Run the polypharmacy risk score tool
2. Get structured data via Analyst (labs, medications, diagnoses)
3. Search clinical notes for additional context
4. Search drug interaction guidelines for flagged medication pairs

ALWAYS use multiple tools to cross-validate answers. Single-source answers are insufficient
for clinical decision support.
',
    SAMPLE_QUESTIONS = (
      'What medications is Eleanor Vance currently taking?',
      'What is the polypharmacy risk for member M010?',
      'Is member M014 compliant with benzodiazepine prescribing policies?',
      'Show me the drug interactions for member M002',
      'Are there any contradictions between structured data and clinical notes for member M010?',
      'Which elderly members have the highest polypharmacy risk?'
    )
  )
  ORCHESTRATION = (
    BUDGET = (SECONDS = 60, TOKENS = 32000),
    CAPABILITIES = (ANALYTICAL_SEARCH = TRUE)
  )
  TOOLS = (
    -- Tool 1: Cortex Analyst for structured data queries
    (
      TOOL_SPEC = (
        TYPE = 'cortex_analyst_text_to_sql',
        NAME = 'clinical_analyst',
        DESCRIPTION = 'Query structured clinical data: member demographics, encounters, medications, diagnoses, and lab results. Use this for factual lookups like active medications, lab values, diagnosis history, and member profiles. Returns SQL-generated results from the semantic view.'
      )
    ),
    -- Tool 2: Clinical Notes Search
    (
      TOOL_SPEC = (
        TYPE = 'cortex_search',
        NAME = 'clinical_notes_search',
        DESCRIPTION = 'Search unstructured clinical notes (progress notes, discharge summaries, consult notes). Use to find clinical narrative context, provider observations, and patient-reported information. Filter by member_id to scope to a specific patient. Use to corroborate or check for contradictions with structured data.'
      )
    ),
    -- Tool 3: Policy Documents Search
    (
      TOOL_SPEC = (
        TYPE = 'cortex_search',
        NAME = 'policy_docs_search',
        DESCRIPTION = 'Search health plan policy documents including formulary rules, prior authorization criteria, step therapy protocols, and coverage policies. Use for compliance checks, determining if a medication requires prior auth, or finding clinical guidelines.'
      )
    ),
    -- Tool 4: Drug Interaction Guidelines Search
    (
      TOOL_SPEC = (
        TYPE = 'cortex_search',
        NAME = 'drug_interaction_search',
        DESCRIPTION = 'Search drug interaction guidelines and warnings. Use to find interaction severity, mechanisms, and management recommendations for specific drug pairs. Filter by severity for critical interactions only.'
      )
    ),
    -- Tool 5: Polypharmacy Risk Scoring (custom UDF)
    (
      TOOL_SPEC = (
        TYPE = 'generic',
        NAME = 'score_polypharmacy_risk',
        DESCRIPTION = 'Calculate polypharmacy risk score for a member. Returns risk level (low/moderate/high), active medication count, list of active medications, flagged drug interactions with severity, and clinical reasoning. Use for any risk assessment query.',
        INPUT_SCHEMA = (
          TYPE = 'object',
          PROPERTIES = (
            member_id = (TYPE = 'string', DESCRIPTION = 'The member ID to assess (e.g., M001)')
          ),
          REQUIRED = ('member_id')
        )
      )
    ),
    -- Tool 6: Policy Compliance Check (custom UDF)
    (
      TOOL_SPEC = (
        TYPE = 'generic',
        NAME = 'check_policy_compliance',
        DESCRIPTION = 'Check if a specific medication for a member complies with health plan formulary and coverage policies. Returns compliance status, applicable policies, specific compliance checks performed, and identified gaps. Use for formulary and prior auth questions.',
        INPUT_SCHEMA = (
          TYPE = 'object',
          PROPERTIES = (
            member_id = (TYPE = 'string', DESCRIPTION = 'The member ID to check'),
            drug_name = (TYPE = 'string', DESCRIPTION = 'The drug name to check compliance for (e.g., Warfarin, Lorazepam)')
          ),
          REQUIRED = ('member_id', 'drug_name')
        )
      )
    )
  )
  TOOL_RESOURCES = (
    'clinical_analyst' = (
      SEMANTIC_VIEW = 'CLINICAL_COPILOT.CORE.CLINICAL_SEMANTIC_VIEW',
      EXECUTION_ENVIRONMENT = (TYPE = 'warehouse', WAREHOUSE = 'COPILOT_WH')
    ),
    'clinical_notes_search' = (
      SEARCH_SERVICE = 'CLINICAL_COPILOT.CORE.CLINICAL_NOTES_SEARCH',
      MAX_RESULTS = 10,
      TITLE_COLUMN = 'note_type',
      ID_COLUMN = 'note_id'
    ),
    'policy_docs_search' = (
      SEARCH_SERVICE = 'CLINICAL_COPILOT.CORE.POLICY_DOCS_SEARCH',
      MAX_RESULTS = 5,
      TITLE_COLUMN = 'policy_name',
      ID_COLUMN = 'doc_id'
    ),
    'drug_interaction_search' = (
      SEARCH_SERVICE = 'CLINICAL_COPILOT.CORE.DRUG_INTERACTION_SEARCH',
      MAX_RESULTS = 10,
      TITLE_COLUMN = 'drug_pair',
      ID_COLUMN = 'guideline_id'
    ),
    'score_polypharmacy_risk' = (
      TYPE = 'function',
      EXECUTION_ENVIRONMENT = (TYPE = 'warehouse', WAREHOUSE = 'COPILOT_WH'),
      IDENTIFIER = 'CLINICAL_COPILOT.CORE.SCORE_POLYPHARMACY_RISK'
    ),
    'check_policy_compliance' = (
      TYPE = 'function',
      EXECUTION_ENVIRONMENT = (TYPE = 'warehouse', WAREHOUSE = 'COPILOT_WH'),
      IDENTIFIER = 'CLINICAL_COPILOT.CORE.CHECK_POLICY_COMPLIANCE'
    )
  );

-- Verify the agent was created
SHOW AGENTS IN SCHEMA CLINICAL_COPILOT.CORE;
DESCRIBE AGENT CLINICAL_COPILOT.CORE.CLINICAL_COPILOT_AGENT;
