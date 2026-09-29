"""
utils/data_loader.py
All cached Snowpark queries for INSURANCE_C360 schema.
Source: MDB_DATA | Enriched: SILVER | Analytics: GOLD
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd

DB  = "INSURANCE_C360"
SRC = "MDB_DATA"
SLV = "SILVER"
GLD = "GOLD"

_session = None
def get_session():
    global _session
    if _session is None:
        _session = get_active_session()
    return _session


# ── Customer 360 queries ──────────────────────────────────────

@st.cache_data(ttl=300)
def load_all_customers_summary():
    return get_session().sql(f"""
        SELECT CUSTOMER_ID, NAME, CITY, STATE, SEGMENT,
               INCOME_BAND, CHURN_RISK_LABEL, NBA_PRIORITY
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        ORDER BY NAME
    """).to_pandas()


@st.cache_data(ttl=300)
def load_customer_360(customer_id: str) -> pd.Series:
    df = get_session().sql(f"""
        SELECT * FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        WHERE CUSTOMER_ID = '{customer_id}'
    """).to_pandas()
    return df.iloc[0] if not df.empty else None


@st.cache_data(ttl=300)
def load_all_360():
    return get_session().sql(f"""
        SELECT * FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        ORDER BY CHURN_RISK_SCORE DESC
    """).to_pandas()


# ── Source table detail queries ───────────────────────────────

@st.cache_data(ttl=300)
def load_customer_policies(customer_id: str) -> pd.DataFrame:
    return get_session().sql(f"""
        SELECT POLICY_ID, POLICY_TYPE, STATUS,
               PREMIUM, SUM_INSURED,
               POLICY_START_DATE, POLICY_END_DATE
        FROM {DB}.{SRC}.POLICY
        WHERE CUSTOMER_ID = '{customer_id}'
        ORDER BY POLICY_START_DATE DESC
    """).to_pandas()


@st.cache_data(ttl=300)
def load_customer_claims(customer_id: str) -> pd.DataFrame:
    return get_session().sql(f"""
        SELECT cl.CLAIM_ID, cl.CLAIM_DATE, cl.CLAIM_TYPE,
               cl.CLAIM_AMOUNT, cl.CLAIM_STATUS,
               cl.CLAIM_DESCRIPTION, p.POLICY_TYPE
        FROM {DB}.{SRC}.CLAIM cl
        JOIN {DB}.{SRC}.POLICY p ON p.POLICY_ID = cl.POLICY_ID
        WHERE cl.CUSTOMER_ID = '{customer_id}'
        ORDER BY cl.CLAIM_DATE DESC
    """).to_pandas()


@st.cache_data(ttl=300)
def load_customer_payments(customer_id: str) -> pd.DataFrame:
    return get_session().sql(f"""
        SELECT PAYMENT_ID, PAYMENT_DATE, AMOUNT,
               PAYMENT_STATUS, p.POLICY_TYPE
        FROM {DB}.{SRC}.PAYMENT pay
        JOIN {DB}.{SRC}.POLICY p ON p.POLICY_ID = pay.POLICY_ID
        WHERE pay.CUSTOMER_ID = '{customer_id}'
        ORDER BY PAYMENT_DATE DESC
        LIMIT 20
    """).to_pandas()


@st.cache_data(ttl=300)
def load_customer_interactions(customer_id: str) -> pd.DataFrame:
    return get_session().sql(f"""
        SELECT INTERACTION_ID, INTERACTION_DATE,
               CHANNEL, AGENT_ID, SUBJECT
        FROM {DB}.{SRC}.INTERACTION
        WHERE CUSTOMER_ID = '{customer_id}'
        ORDER BY INTERACTION_DATE DESC
        LIMIT 15
    """).to_pandas()


@st.cache_data(ttl=300)
def load_customer_transcripts(customer_id: str) -> pd.DataFrame:
    return get_session().sql(f"""
        SELECT e.CALL_ID, e.INTERACTION_DATE, e.CHANNEL,
               e.SUBJECT, e.SENTIMENT_SCORE, e.CUSTOMER_INTENT,
               e.CALL_SUMMARY, e.KEY_TOPICS,
               e.RESOLUTION_FLAG, e.TRANSCRIPT_TEXT
        FROM {DB}.{SLV}.ENRICHED_TRANSCRIPTS e
        WHERE e.CUSTOMER_ID = '{customer_id}'
        ORDER BY e.INTERACTION_DATE DESC
        LIMIT 10
    """).to_pandas()


# ── Analytics / segment queries ───────────────────────────────

@st.cache_data(ttl=600)
def load_segment_analytics():
    return get_session().sql(f"""
        SELECT
          SEGMENT,
          COUNT(*)                                AS CUSTOMER_COUNT,
          ROUND(AVG(CHURN_RISK_SCORE)*100, 1)    AS AVG_CHURN_RISK_PCT,
          ROUND(AVG(LIFETIME_VALUE), 0)           AS AVG_LTV,
          ROUND(SUM(LIFETIME_VALUE), 0)           AS TOTAL_LTV,
          COUNT_IF(CHURN_RISK_LABEL='High')       AS HIGH_RISK_COUNT,
          ROUND(AVG(AVG_SENTIMENT_SCORE), 3)      AS AVG_SENTIMENT,
          SUM(CASE WHEN CHURN_RISK_LABEL='High'
                   THEN LIFETIME_VALUE ELSE 0 END) AS LTV_AT_RISK,
          ROUND(AVG(TOTAL_ACTIVE_PREMIUM), 0)     AS AVG_PREMIUM
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        GROUP BY SEGMENT
        ORDER BY AVG_CHURN_RISK_PCT DESC
    """).to_pandas()


@st.cache_data(ttl=600)
def load_nba_distribution():
    return get_session().sql(f"""
        SELECT
          NBA_PRIORITY, NBA_CHANNEL, NBA_ACTION,
          COUNT(*)                               AS CUSTOMER_COUNT,
          ROUND(AVG(CHURN_RISK_SCORE)*100, 1)   AS AVG_CHURN_PCT,
          ROUND(SUM(LIFETIME_VALUE), 0)          AS TOTAL_LTV
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        GROUP BY NBA_PRIORITY, NBA_CHANNEL, NBA_ACTION
        ORDER BY CUSTOMER_COUNT DESC
    """).to_pandas()


@st.cache_data(ttl=600)
def load_sentiment_trend():
    return get_session().sql(f"""
        SELECT
          DATE_TRUNC('month', INTERACTION_DATE)  AS MONTH,
          ROUND(AVG(SENTIMENT_SCORE), 3)         AS AVG_SENTIMENT,
          COUNT(*)                               AS CALL_COUNT,
          COUNT_IF(SENTIMENT_SCORE < -0.3)       AS NEGATIVE_CALLS,
          COUNT_IF(CUSTOMER_INTENT='complaint')  AS COMPLAINT_CALLS
        FROM {DB}.{SLV}.ENRICHED_TRANSCRIPTS
        GROUP BY 1
        ORDER BY 1
    """).to_pandas()


@st.cache_data(ttl=600)
def load_claim_severity():
    """Scenario 4 — claim severity by policy type."""
    return get_session().sql(f"""
        SELECT
          p.POLICY_TYPE,
          COUNT(cl.CLAIM_ID)                     AS TOTAL_CLAIMS,
          ROUND(AVG(cl.CLAIM_AMOUNT), 2)         AS AVG_CLAIM_AMOUNT,
          SUM(cl.CLAIM_AMOUNT)                   AS TOTAL_CLAIM_AMOUNT,
          COUNT_IF(cl.CLAIM_STATUS IN ('Approved','Paid')) AS APPROVED,
          ROUND(COUNT_IF(cl.CLAIM_STATUS IN ('Approved','Paid'))::FLOAT
                / NULLIF(COUNT(cl.CLAIM_ID),0)*100, 1) AS APPROVAL_RATE_PCT
        FROM {DB}.{SRC}.CLAIM cl
        JOIN {DB}.{SRC}.POLICY p ON p.POLICY_ID = cl.POLICY_ID
        GROUP BY p.POLICY_TYPE
        ORDER BY AVG_CLAIM_AMOUNT DESC
    """).to_pandas()


@st.cache_data(ttl=600)
def load_lapses_by_state():
    """Scenario 8 — policy lapses by state."""
    return get_session().sql(f"""
        SELECT
          c.STATE, c.SEGMENT,
          COUNT(*)                               AS LAPSED_COUNT,
          ROUND(AVG(c.CHURN_RISK), 3)           AS AVG_CHURN_RISK
        FROM {DB}.{SRC}.POLICY p
        JOIN {DB}.{SRC}.INSURANCE_CUSTOMER c ON c.CUSTOMER_ID = p.CUSTOMER_ID
        WHERE p.STATUS IN ('Cancelled','Lapsed')
        GROUP BY c.STATE, c.SEGMENT
        ORDER BY LAPSED_COUNT DESC
    """).to_pandas()


@st.cache_data(ttl=600)
def load_channel_effectiveness():
    """Scenario 9 — channel complaint rate."""
    return get_session().sql(f"""
        SELECT
          CHANNEL,
          COUNT(*)                               AS TOTAL_INTERACTIONS,
          COUNT_IF(SUBJECT ILIKE 'Complaint%')   AS COMPLAINT_COUNT,
          ROUND(COUNT_IF(SUBJECT ILIKE 'Complaint%')::FLOAT
                / NULLIF(COUNT(*),0)*100, 1)     AS COMPLAINT_RATE_PCT
        FROM {DB}.{SRC}.INTERACTION
        GROUP BY CHANNEL
        ORDER BY COMPLAINT_RATE_PCT DESC
    """).to_pandas()


@st.cache_data(ttl=600)
def load_income_band_analysis():
    return get_session().sql(f"""
        SELECT
          INCOME_BAND,
          COUNT(*)                               AS CUSTOMERS,
          ROUND(AVG(CHURN_RISK_SCORE)*100, 1)   AS AVG_CHURN_PCT,
          ROUND(AVG(LIFETIME_VALUE), 0)          AS AVG_LTV,
          COUNT_IF(CHURN_RISK_LABEL='High')      AS HIGH_RISK_COUNT
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        GROUP BY INCOME_BAND
        ORDER BY AVG_CHURN_PCT DESC
    """).to_pandas()


@st.cache_data(ttl=600)
def load_daily_log():
    return get_session().sql(f"""
        SELECT * FROM {DB}.{GLD}.NBA_DAILY_LOG
        ORDER BY LOG_DATE DESC LIMIT 30
    """).to_pandas()


# ── Live Cortex AI generation ─────────────────────────────────

def generate_nba_message(row: pd.Series) -> str:
    prompt = (
        "You are a customer relationship manager at an insurance company. "
        "Write a personalised 2-sentence outreach message. Warm, specific, professional. "
        "No generic phrases. Output ONLY the message text."
        f" Customer: {row['NAME']}"
        f" | Segment: {row['SEGMENT']}"
        f" | Tenure: {row['TENURE_DAYS']} days"
        f" | Policies: {row['ACTIVE_POLICY_TYPES']}"
        f" | Action: {row['NBA_ACTION']}"
        f" | Reason: {row['NBA_REASON']}"
    ).replace("'", "''")
    result = get_session().sql(f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{prompt}') AS MSG
    """).to_pandas()
    return result["MSG"].iloc[0] if not result.empty else "Unable to generate."
