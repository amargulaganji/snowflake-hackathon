import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="SnowCare360 Dashboard", layout="wide")

session = get_active_session()


@st.cache_data(ttl=300)
def load_risk_summary():
    return session.sql("""
        SELECT m.MEMBER_ID, m.FIRST_NAME, m.LAST_NAME, m.AGE, m.GENDER,
               m.PLAN_TYPE, m.RISK_FLAGS,
               s.ACTIVE_MEDICATION_COUNT, s.ACTIVE_DIAGNOSIS_COUNT,
               s.ABNORMAL_LAB_COUNT, s.RECENT_ENCOUNTER_COUNT,
               s.TOTAL_CLAIM_COUNT, s.DOCUMENT_COUNT
        FROM MEMBER m
        LEFT JOIN MEMBER_360_SUMMARY s ON m.MEMBER_ID = s.MEMBER_ID
        ORDER BY s.ACTIVE_MEDICATION_COUNT DESC NULLS LAST
        LIMIT 50
    """).to_pandas()


@st.cache_data(ttl=300)
def load_kpis():
    row = session.sql("""
        SELECT COUNT(*) AS total_members,
               SUM(CASE WHEN ARRAY_SIZE(RISK_FLAGS) >= 3 THEN 1 ELSE 0 END) AS high_risk,
               AVG(AGE) AS avg_age
        FROM MEMBER
    """).to_pandas().iloc[0]
    meds = session.sql("""
        SELECT COUNT(*) AS total_active
        FROM MEDICATION WHERE STATUS = 'active'
    """).to_pandas().iloc[0]
    labs = session.sql("""
        SELECT SUM(CASE WHEN ABNORMAL_FLAG = TRUE THEN 1 ELSE 0 END) AS abnormal,
               COUNT(*) AS total
        FROM LAB_RESULT
    """).to_pandas().iloc[0]
    audit = session.sql("SELECT COUNT(*) AS cnt FROM AI_AUDIT_LOG").to_pandas().iloc[0]
    return row, meds, labs, audit


@st.cache_data(ttl=300)
def load_risk_distribution():
    return session.sql("""
        SELECT
            CASE
                WHEN ARRAY_SIZE(RISK_FLAGS) >= 3 THEN 'High'
                WHEN ARRAY_SIZE(RISK_FLAGS) >= 1 THEN 'Moderate'
                ELSE 'Low'
            END AS RISK_LEVEL,
            COUNT(*) AS MEMBER_COUNT
        FROM MEMBER
        GROUP BY RISK_LEVEL
        ORDER BY MEMBER_COUNT DESC
    """).to_pandas()


@st.cache_data(ttl=300)
def load_med_status():
    return session.sql("""
        SELECT STATUS, COUNT(*) AS COUNT
        FROM MEDICATION
        GROUP BY STATUS
        ORDER BY COUNT DESC
    """).to_pandas()


@st.cache_data(ttl=300)
def load_top_drugs():
    return session.sql("""
        SELECT DRUG_NAME, COUNT(*) AS PRESCRIPTIONS
        FROM MEDICATION
        WHERE STATUS = 'active'
        GROUP BY DRUG_NAME
        ORDER BY PRESCRIPTIONS DESC
        LIMIT 10
    """).to_pandas()


@st.cache_data(ttl=300)
def load_abnormal_labs():
    return session.sql("""
        SELECT TEST_NAME, COUNT(*) AS ABNORMAL_COUNT
        FROM LAB_RESULT
        WHERE ABNORMAL_FLAG = TRUE
        GROUP BY TEST_NAME
        ORDER BY ABNORMAL_COUNT DESC
        LIMIT 10
    """).to_pandas()


@st.cache_data(ttl=300)
def load_encounters_by_type():
    return session.sql("""
        SELECT ENCOUNTER_TYPE, COUNT(*) AS COUNT
        FROM ENCOUNTER
        GROUP BY ENCOUNTER_TYPE
        ORDER BY COUNT DESC
    """).to_pandas()


@st.cache_data(ttl=300)
def load_plan_distribution():
    return session.sql("""
        SELECT PLAN_TYPE, COUNT(*) AS MEMBERS
        FROM MEMBER
        GROUP BY PLAN_TYPE
        ORDER BY MEMBERS DESC
    """).to_pandas()


@st.cache_data(ttl=300)
def load_recent_audit():
    return session.sql("""
        SELECT USER_ID, USER_ROLE, MEMBER_ID, ACTION,
               LEFT(QUESTION, 80) AS QUESTION,
               TOOLS_INVOKED, RISK_LEVEL,
               CONTRADICTION_DETECTED, INSUFFICIENT_EVIDENCE,
               LATENCY_MS,
               TO_VARCHAR(TIMESTAMP, 'YYYY-MM-DD HH24:MI') AS TIMESTAMP
        FROM AI_AUDIT_LOG
        ORDER BY TIMESTAMP DESC
        LIMIT 20
    """).to_pandas()


@st.cache_data(ttl=300)
def load_task_history():
    return session.sql("""
        SELECT NAME, STATE,
               TO_VARCHAR(TO_TIMESTAMP(SCHEDULED_TIME), 'YYYY-MM-DD HH24:MI') AS SCHEDULED,
               TO_VARCHAR(TO_TIMESTAMP(COMPLETED_TIME), 'YYYY-MM-DD HH24:MI') AS COMPLETED,
               ERROR_MESSAGE
        FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(RESULT_LIMIT => 10))
        WHERE DATABASE_NAME = 'CLINICAL_COPILOT'
        ORDER BY SCHEDULED_TIME DESC
    """).to_pandas()


# --- Header ---
st.title("SnowCare360 Clinical Intelligence Dashboard")
st.caption("Snowflake-native healthcare analytics powered by Cortex AI")

# --- KPIs ---
member_kpi, med_kpi, lab_kpi, audit_kpi = load_kpis()
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Members", int(member_kpi["TOTAL_MEMBERS"]))
k2.metric("High Risk", int(member_kpi["HIGH_RISK"]))
k3.metric("Active Medications", int(med_kpi["TOTAL_ACTIVE"]))
k4.metric("Abnormal Labs", int(lab_kpi["ABNORMAL"]))
k5.metric("AI Queries Logged", int(audit_kpi["CNT"]))

st.divider()

# --- Risk & Plan Distribution ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Risk Distribution")
    risk_df = load_risk_distribution()
    st.bar_chart(risk_df, x="RISK_LEVEL", y="MEMBER_COUNT", color="RISK_LEVEL")
with col2:
    st.subheader("Plan Type Distribution")
    plan_df = load_plan_distribution()
    st.bar_chart(plan_df, x="PLAN_TYPE", y="MEMBERS", color="PLAN_TYPE")

# --- Medications & Labs ---
col3, col4 = st.columns(2)
with col3:
    st.subheader("Top 10 Active Medications")
    drugs_df = load_top_drugs()
    st.bar_chart(drugs_df, x="DRUG_NAME", y="PRESCRIPTIONS")
with col4:
    st.subheader("Most Common Abnormal Labs")
    labs_df = load_abnormal_labs()
    st.bar_chart(labs_df, x="TEST_NAME", y="ABNORMAL_COUNT")

# --- Encounter & Medication Status ---
col5, col6 = st.columns(2)
with col5:
    st.subheader("Encounters by Type")
    enc_df = load_encounters_by_type()
    st.bar_chart(enc_df, x="ENCOUNTER_TYPE", y="COUNT")
with col6:
    st.subheader("Medication Status Breakdown")
    med_df = load_med_status()
    st.bar_chart(med_df, x="STATUS", y="COUNT")

st.divider()

# --- Member Risk Table ---
st.subheader("Member Risk Overview")
df = load_risk_summary()
if not df.empty:
    st.dataframe(
        df[["MEMBER_ID", "FIRST_NAME", "LAST_NAME", "AGE", "GENDER", "PLAN_TYPE",
            "ACTIVE_MEDICATION_COUNT", "ACTIVE_DIAGNOSIS_COUNT", "ABNORMAL_LAB_COUNT",
            "RECENT_ENCOUNTER_COUNT", "DOCUMENT_COUNT"]],
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# --- AI Audit Log ---
st.subheader("Recent AI Agent Activity")
audit_df = load_recent_audit()
if audit_df.empty:
    st.info("No AI agent queries logged yet. Ask a question in the main app to generate audit entries.")
else:
    st.dataframe(audit_df, use_container_width=True, hide_index=True)

# --- Task History ---
st.subheader("Scheduled Task History")
try:
    task_df = load_task_history()
    if task_df.empty:
        st.info("No recent task executions found.")
    else:
        st.dataframe(task_df, use_container_width=True, hide_index=True)
except Exception:
    st.info("Task history not available.")

# --- Footer ---
st.divider()
st.caption("SnowCare360 | Built with Snowflake CoCo | All data is synthetic")
