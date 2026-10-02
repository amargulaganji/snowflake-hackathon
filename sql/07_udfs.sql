-- 07_udfs.sql: Custom UDFs for the Cortex Agent tools
USE DATABASE CLINICAL_COPILOT;
USE SCHEMA CORE;
USE WAREHOUSE COPILOT_WH;

-- ============================================================
-- 1. SCORE_POLYPHARMACY_RISK
-- Returns a JSON risk assessment for a given member based on
-- their active medications and known drug interactions.
-- ============================================================
CREATE OR REPLACE FUNCTION SCORE_POLYPHARMACY_RISK(P_MEMBER_ID VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
AS
$$
  SELECT OBJECT_CONSTRUCT(
    'member_id', P_MEMBER_ID,
    'risk_level',
      CASE
        WHEN active_count >= 10 THEN 'high'
        WHEN active_count >= 7 THEN 'high'
        WHEN active_count >= 5 THEN 'moderate'
        ELSE 'low'
      END,
    'active_medication_count', active_count,
    'active_medications', med_list,
    'flagged_interactions', interactions,
    'reasoning',
      CASE
        WHEN active_count >= 10 THEN
          'CRITICAL: Member has ' || active_count::VARCHAR || ' active medications. '
          || 'This significantly exceeds the polypharmacy threshold of 5. '
          || 'Immediate comprehensive medication review (CMR) recommended per CMS guidelines.'
        WHEN active_count >= 7 THEN
          'HIGH RISK: Member has ' || active_count::VARCHAR || ' active medications with known drug interactions. '
          || 'Pharmacist-led medication therapy management (MTM) recommended.'
        WHEN active_count >= 5 THEN
          'MODERATE RISK: Member meets polypharmacy criteria with ' || active_count::VARCHAR || ' active medications. '
          || 'Annual medication review recommended.'
        ELSE
          'LOW RISK: Member has ' || active_count::VARCHAR || ' active medications, below polypharmacy threshold.'
      END
  )
  FROM (
    SELECT
      COUNT(*) AS active_count,
      ARRAY_AGG(OBJECT_CONSTRUCT(
        'drug_name', drug_name,
        'dosage', dosage,
        'frequency', frequency,
        'prescriber', prescriber
      )) AS med_list
    FROM CLINICAL_COPILOT.CORE.MEDICATION
    WHERE member_id = P_MEMBER_ID AND status = 'active'
  ) meds,
  LATERAL (
    SELECT COALESCE(ARRAY_AGG(OBJECT_CONSTRUCT(
      'drug_pair', g.drug_pair,
      'severity', g.severity,
      'description', g.description,
      'source', g.source
    )), ARRAY_CONSTRUCT()) AS interactions
    FROM CLINICAL_COPILOT.CORE.MEDICATION m1
    JOIN CLINICAL_COPILOT.CORE.MEDICATION m2
      ON m1.member_id = m2.member_id
      AND m1.medication_id < m2.medication_id
      AND m1.status = 'active' AND m2.status = 'active'
    JOIN CLINICAL_COPILOT.CORE.DRUG_INTERACTION_GUIDELINE g
      ON (g.drug_pair ILIKE '%' || m1.drug_name || '%'
          AND g.drug_pair ILIKE '%' || m2.drug_name || '%')
    WHERE m1.member_id = P_MEMBER_ID
  ) ints
$$;

-- ============================================================
-- 2. CHECK_POLICY_COMPLIANCE
-- Checks if a member's medication usage complies with plan
-- formulary and coverage policies. Returns compliance status
-- with specific policy references and identified gaps.
-- ============================================================
CREATE OR REPLACE FUNCTION CHECK_POLICY_COMPLIANCE(P_MEMBER_ID VARCHAR, P_DRUG_NAME VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
AS
$$
  SELECT OBJECT_CONSTRUCT(
    'member_id', P_MEMBER_ID,
    'drug_name', P_DRUG_NAME,
    'medication_found', med_found,
    'medication_status', med_status,
    'relevant_policies', policies,
    'compliance_checks', checks,
    'overall_compliant',
      CASE WHEN ARRAY_SIZE(gaps) = 0 AND med_found THEN TRUE ELSE FALSE END,
    'gaps', gaps,
    'reasoning',
      CASE
        WHEN NOT med_found THEN
          'No active prescription for ' || P_DRUG_NAME || ' found for this member.'
        WHEN ARRAY_SIZE(gaps) > 0 THEN
          'COMPLIANCE GAPS IDENTIFIED: ' || ARRAY_SIZE(gaps)::VARCHAR || ' issue(s) found. Review required.'
        ELSE
          'Member appears compliant with applicable policies for ' || P_DRUG_NAME || '.'
      END
  )
  FROM (
    SELECT
      COUNT(*) > 0 AS med_found,
      MAX(status) AS med_status
    FROM CLINICAL_COPILOT.CORE.MEDICATION
    WHERE member_id = P_MEMBER_ID
      AND LOWER(drug_name) = LOWER(P_DRUG_NAME)
      AND status = 'active'
  ) med_info,
  LATERAL (
    SELECT COALESCE(ARRAY_AGG(OBJECT_CONSTRUCT(
      'policy_name', pd.policy_name,
      'category', pd.category,
      'topic', pd.topic,
      'effective_date', pd.effective_date::VARCHAR
    )), ARRAY_CONSTRUCT()) AS policies
    FROM CLINICAL_COPILOT.CORE.POLICY_DOCUMENT pd
    WHERE pd.content_text ILIKE '%' || P_DRUG_NAME || '%'
       OR pd.topic ILIKE '%' || P_DRUG_NAME || '%'
       OR (P_DRUG_NAME ILIKE '%statin%' AND pd.topic = 'statins')
       OR (P_DRUG_NAME ILIKE '%warfarin%' AND pd.topic = 'anticoagulation')
       OR (P_DRUG_NAME ILIKE '%lorazepam%' AND pd.topic = 'benzodiazepines')
       OR (P_DRUG_NAME ILIKE '%metformin%' AND pd.topic IN ('diabetes', 'renal'))
  ) pol,
  LATERAL (
    SELECT COALESCE(ARRAY_AGG(check_item), ARRAY_CONSTRUCT()) AS checks,
           COALESCE(ARRAY_AGG(CASE WHEN is_gap THEN check_item END), ARRAY_CONSTRUCT()) AS gaps
    FROM (
      -- Check 1: Beers Criteria for elderly + benzodiazepines
      SELECT
        OBJECT_CONSTRUCT(
          'check', 'Beers Criteria — benzodiazepine in elderly',
          'result', 'FAIL — prior authorization required',
          'policy', 'Benzodiazepine Use in Elderly'
        ) AS check_item,
        TRUE AS is_gap
      WHERE LOWER(P_DRUG_NAME) IN ('lorazepam','alprazolam','diazepam','clonazepam')
        AND EXISTS (SELECT 1 FROM CLINICAL_COPILOT.CORE.MEMBER WHERE member_id = P_MEMBER_ID AND age >= 65)

      UNION ALL

      -- Check 2: Metformin contraindication in severe CKD
      SELECT
        OBJECT_CONSTRUCT(
          'check', 'CKD Medication Adjustment — Metformin contraindication',
          'result', 'FAIL — eGFR below safe threshold',
          'policy', 'CKD Medication Adjustment Protocol'
        ),
        TRUE
      WHERE LOWER(P_DRUG_NAME) = 'metformin'
        AND EXISTS (
          SELECT 1 FROM CLINICAL_COPILOT.CORE.LAB_RESULT
          WHERE member_id = P_MEMBER_ID AND test_name = 'eGFR'
            AND result_value < 30
            AND result_date = (
              SELECT MAX(result_date) FROM CLINICAL_COPILOT.CORE.LAB_RESULT
              WHERE member_id = P_MEMBER_ID AND test_name = 'eGFR'
            )
        )

      UNION ALL

      -- Check 3: Warfarin monitoring compliance
      SELECT
        OBJECT_CONSTRUCT(
          'check', 'Warfarin INR monitoring frequency',
          'result', CASE WHEN last_inr_date < DATEADD(day, -42, CURRENT_DATE())
                        THEN 'FAIL — INR not checked within 6 weeks'
                        ELSE 'PASS — INR monitoring current' END,
          'policy', 'Warfarin Management Policy'
        ),
        last_inr_date < DATEADD(day, -42, CURRENT_DATE())
      FROM (
        SELECT MAX(result_date) AS last_inr_date
        FROM CLINICAL_COPILOT.CORE.LAB_RESULT
        WHERE member_id = P_MEMBER_ID AND test_name = 'INR'
      )
      WHERE LOWER(P_DRUG_NAME) = 'warfarin'
        AND last_inr_date IS NOT NULL

      UNION ALL

      -- Check 4: Statin step therapy
      SELECT
        OBJECT_CONSTRUCT(
          'check', 'Statin step therapy — generic preferred',
          'result', 'PASS — generic statin in use',
          'policy', 'Statin Therapy Guidelines'
        ),
        FALSE
      WHERE LOWER(P_DRUG_NAME) IN ('atorvastatin','rosuvastatin','pravastatin','simvastatin')
    )
  ) compliance
$$;
