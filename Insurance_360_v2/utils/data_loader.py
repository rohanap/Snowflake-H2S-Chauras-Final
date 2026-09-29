"""
utils/data_loader.py
All cached Snowpark queries for INSURANCE_C360 schema.
Source: MDB_DATA | Enriched: SILVER | Analytics: GOLD

Conventions in this module:
  * The Snowflake session comes from st.connection (the supported pattern for
    Streamlit in Snowflake / Workspace container runtime), cached as a resource.
  * Every value that originates from a widget is passed as a BOUND PARAMETER
    (`?` placeholders + params=[...]), never interpolated into the SQL string.
  * Every loader is memoized with an explicit ttl, and per-customer loaders
    also carry max_entries so the cache cannot grow unbounded.
"""
import os

import pandas as pd
import streamlit as st

DB = "INSURANCE_C360"
SRC = "MDB_DATA"
SLV = "SILVER"
GLD = "GOLD"

# Columns actually consumed by the NBA dashboard + triage cards + message
# generation. The view has 58 columns; pulling all of them for 1,000 rows was
# ~2.5x more payload than any page renders.
#
# NBA_MESSAGE is deliberately EXCLUDED: it averages 296 chars x 1,000 rows =
# 289 KB, which was ~74% of the whole text payload, and the dashboard only ever
# displays one message at a time. Fetch it per customer via load_nba_message().
_C360_COLS = """
    CUSTOMER_ID, NAME, CITY, STATE, SEGMENT, INCOME_BAND,
    TENURE_DAYS, LIFETIME_VALUE,
    ACTIVE_POLICY_COUNT, ACTIVE_POLICY_TYPE_COUNT, ACTIVE_POLICY_TYPES,
    TOTAL_ACTIVE_PREMIUM,
    OPEN_CLAIMS, FAILED_PAYMENT_COUNT,
    COMPLAINT_COUNT, TOTAL_CALLS, AVG_SENTIMENT_SCORE,
    CHURN_RISK_SCORE, CHURN_RISK_LABEL, UPSELL_PROBABILITY,
    NBA_PRIORITY, NBA_ACTION, NBA_REASON, NBA_CHANNEL
"""

# Cache lifetimes are generous on purpose. Every distinct query against
# GOLD.CUSTOMER_360_VIEW costs 2-5s in Snowflake COMPILE time (it sits on top of
# CUSTOMER_360_BASE -> four FACT_* views -> SILVER dynamic tables), so a short
# TTL means re-paying that mid-session. Use the sidebar "Refresh data" button
# (clear_all_caches) to force a fresh read on demand.
_TTL_ROWS = 900      # per-customer and row-level reads
_TTL_AGG = 1800      # aggregates that move slowly


@st.cache_resource
def _connection():
    """Embedded Snowflake identity provided by the platform."""
    return st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))


def get_session():
    """Snowpark session, for callers that need the Snowpark/Root API."""
    return _connection().session()


def _q(sql: str, params: list | None = None) -> pd.DataFrame:
    """Run SQL with bound parameters and return a pandas DataFrame."""
    return get_session().sql(sql, params=params or []).to_pandas()


# Public alias for pages that define their own cached loaders.
run_query = _q


# ── Customer 360 queries ──────────────────────────────────────

@st.cache_data(ttl=_TTL_ROWS, show_spinner=False)
def load_all_customers_summary() -> pd.DataFrame:
    """Lightweight list used to populate the customer picker."""
    return _q(f"""
        SELECT CUSTOMER_ID, NAME, CITY, STATE, SEGMENT,
               INCOME_BAND, CHURN_RISK_LABEL, NBA_PRIORITY
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        ORDER BY NAME
    """)


@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_customer_360(customer_id: str):
    """Full 58-column profile for a single customer."""
    df = _q(f"""
        SELECT * FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        WHERE CUSTOMER_ID = ?
    """, [customer_id])
    return df.iloc[0] if not df.empty else None


@st.cache_data(ttl=_TTL_ROWS, show_spinner=False)
def load_all_360() -> pd.DataFrame:
    """All customers, trimmed to the columns the dashboards actually render."""
    return _q(f"""
        SELECT {_C360_COLS}
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        ORDER BY CHURN_RISK_SCORE DESC
    """)


@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_nba_message(customer_id: str) -> str:
    """Pre-generated outreach message for one customer.

    Kept out of load_all_360() because it is by far the largest column: 289 KB
    across 1,000 rows, of which the UI shows exactly one at a time.
    """
    df = _q(f"""
        SELECT NBA_MESSAGE
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        WHERE CUSTOMER_ID = ?
    """, [customer_id])
    if df.empty or df["NBA_MESSAGE"].iloc[0] is None:
        return ""
    return str(df["NBA_MESSAGE"].iloc[0]).strip()


@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_customer_confidence(customer_id: str):
    """NBA confidence score and explanation for one customer."""
    df = _q(f"""
        SELECT NBA_CONFIDENCE, CONFIDENCE_EXPLANATION
        FROM {DB}.{GLD}.NBA_WITH_CONFIDENCE
        WHERE CUSTOMER_ID = ?
    """, [customer_id])
    if df.empty:
        return None, None
    return float(df["NBA_CONFIDENCE"].iloc[0] or 0), str(df["CONFIDENCE_EXPLANATION"].iloc[0] or "")


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_confidence_summary() -> pd.DataFrame:
    """Confidence distribution across all customers for KPI display."""
    return _q(f"""
        SELECT
          ROUND(AVG(NBA_CONFIDENCE), 3) AS AVG_CONFIDENCE,
          COUNT_IF(NBA_CONFIDENCE >= 0.5) AS HIGH_CONF,
          COUNT_IF(NBA_CONFIDENCE < 0.5) AS LOW_CONF
        FROM {DB}.{GLD}.NBA_WITH_CONFIDENCE
    """)


# ── Source table detail queries ───────────────────────────────

@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_customer_policies(customer_id: str) -> pd.DataFrame:
    return _q(f"""
        SELECT POLICY_ID, POLICY_TYPE, STATUS,
               PREMIUM, SUM_INSURED,
               POLICY_START_DATE, POLICY_END_DATE
        FROM {DB}.{SRC}.POLICY
        WHERE CUSTOMER_ID = ?
        ORDER BY POLICY_START_DATE DESC
    """, [customer_id])


@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_customer_claims(customer_id: str) -> pd.DataFrame:
    return _q(f"""
        SELECT cl.CLAIM_ID, cl.CLAIM_DATE, cl.CLAIM_TYPE,
               cl.CLAIM_AMOUNT, cl.CLAIM_STATUS,
               cl.CLAIM_DESCRIPTION, p.POLICY_TYPE
        FROM {DB}.{SRC}.CLAIM cl
        JOIN {DB}.{SRC}.POLICY p ON p.POLICY_ID = cl.POLICY_ID
        WHERE cl.CUSTOMER_ID = ?
        ORDER BY cl.CLAIM_DATE DESC
    """, [customer_id])


@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_customer_payments(customer_id: str) -> pd.DataFrame:
    return _q(f"""
        SELECT PAYMENT_ID, PAYMENT_DATE, AMOUNT,
               PAYMENT_STATUS, p.POLICY_TYPE
        FROM {DB}.{SRC}.PAYMENT pay
        JOIN {DB}.{SRC}.POLICY p ON p.POLICY_ID = pay.POLICY_ID
        WHERE pay.CUSTOMER_ID = ?
        ORDER BY PAYMENT_DATE DESC
        LIMIT 20
    """, [customer_id])


@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_customer_interactions(customer_id: str) -> pd.DataFrame:
    return _q(f"""
        SELECT INTERACTION_ID, INTERACTION_DATE,
               CHANNEL, AGENT_ID, SUBJECT
        FROM {DB}.{SRC}.INTERACTION
        WHERE CUSTOMER_ID = ?
        ORDER BY INTERACTION_DATE DESC
        LIMIT 15
    """, [customer_id])


@st.cache_data(ttl=_TTL_ROWS, max_entries=100, show_spinner=False)
def load_customer_transcripts(customer_id: str) -> pd.DataFrame:
    return _q(f"""
        SELECT e.CALL_ID, e.INTERACTION_DATE, e.CHANNEL,
               e.SUBJECT, e.SENTIMENT_SCORE, e.CUSTOMER_INTENT,
               e.CALL_SUMMARY, e.KEY_TOPICS,
               e.RESOLUTION_FLAG, e.TRANSCRIPT_TEXT
        FROM {DB}.{SLV}.ENRICHED_TRANSCRIPTS e
        WHERE e.CUSTOMER_ID = ?
        ORDER BY e.INTERACTION_DATE DESC
        LIMIT 10
    """, [customer_id])


# ── Analytics / segment queries ───────────────────────────────

@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_high_value_at_risk(min_churn: float = 0.5,
                            min_ltv: float = 5000,
                            limit: int = 20) -> pd.DataFrame:
    """Scenario 1 — high-LTV customers at churn risk.

    Previously this ran uncached inline on the Segment Analytics page, so it
    re-executed on every widget interaction.
    """
    # min_churn / min_ltv are bound; `limit` is coerced to int because LIMIT
    # binding support is inconsistent across drivers.
    return _q(f"""
        SELECT CUSTOMER_ID, NAME, SEGMENT, LIFETIME_VALUE,
               ROUND(CHURN_RISK_SCORE*100,1) AS CHURN_RISK_PCT,
               CHURN_RISK_LABEL, ACTIVE_POLICY_COUNT, NBA_PRIORITY
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        WHERE CHURN_RISK_SCORE > ? AND LIFETIME_VALUE > ?
        ORDER BY LIFETIME_VALUE DESC, CHURN_RISK_SCORE DESC
        LIMIT {int(limit)}
    """, [min_churn, min_ltv])


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_segment_analytics() -> pd.DataFrame:
    return _q(f"""
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
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_nba_distribution() -> pd.DataFrame:
    return _q(f"""
        SELECT
          NBA_PRIORITY, NBA_CHANNEL, NBA_ACTION,
          COUNT(*)                               AS CUSTOMER_COUNT,
          ROUND(AVG(CHURN_RISK_SCORE)*100, 1)   AS AVG_CHURN_PCT,
          ROUND(SUM(LIFETIME_VALUE), 0)          AS TOTAL_LTV
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        GROUP BY NBA_PRIORITY, NBA_CHANNEL, NBA_ACTION
        ORDER BY CUSTOMER_COUNT DESC
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_sentiment_trend() -> pd.DataFrame:
    return _q(f"""
        SELECT
          DATE_TRUNC('month', INTERACTION_DATE)  AS MONTH,
          ROUND(AVG(SENTIMENT_SCORE), 3)         AS AVG_SENTIMENT,
          COUNT(*)                               AS CALL_COUNT,
          COUNT_IF(SENTIMENT_SCORE < -0.3)       AS NEGATIVE_CALLS,
          COUNT_IF(CUSTOMER_INTENT='complaint')  AS COMPLAINT_CALLS
        FROM {DB}.{SLV}.ENRICHED_TRANSCRIPTS
        GROUP BY 1
        ORDER BY 1
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_claim_severity() -> pd.DataFrame:
    """Scenario 4 — claim severity by policy type."""
    return _q(f"""
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
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_lapses_by_state() -> pd.DataFrame:
    """Scenario 8 — policy lapses by state."""
    return _q(f"""
        SELECT
          c.STATE, c.SEGMENT,
          COUNT(*)                               AS LAPSED_COUNT,
          ROUND(AVG(c.CHURN_RISK), 3)           AS AVG_CHURN_RISK
        FROM {DB}.{SRC}.POLICY p
        JOIN {DB}.{SRC}.INSURANCE_CUSTOMER c ON c.CUSTOMER_ID = p.CUSTOMER_ID
        WHERE p.STATUS IN ('Cancelled','Lapsed')
        GROUP BY c.STATE, c.SEGMENT
        ORDER BY LAPSED_COUNT DESC
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_channel_effectiveness() -> pd.DataFrame:
    """Scenario 9 — channel complaint rate."""
    return _q(f"""
        SELECT
          CHANNEL,
          COUNT(*)                               AS TOTAL_INTERACTIONS,
          COUNT_IF(SUBJECT ILIKE 'Complaint%')   AS COMPLAINT_COUNT,
          ROUND(COUNT_IF(SUBJECT ILIKE 'Complaint%')::FLOAT
                / NULLIF(COUNT(*),0)*100, 1)     AS COMPLAINT_RATE_PCT
        FROM {DB}.{SRC}.INTERACTION
        GROUP BY CHANNEL
        ORDER BY COMPLAINT_RATE_PCT DESC
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_income_band_analysis() -> pd.DataFrame:
    return _q(f"""
        SELECT
          INCOME_BAND,
          COUNT(*)                               AS CUSTOMERS,
          ROUND(AVG(CHURN_RISK_SCORE)*100, 1)   AS AVG_CHURN_PCT,
          ROUND(AVG(LIFETIME_VALUE), 0)          AS AVG_LTV,
          COUNT_IF(CHURN_RISK_LABEL='High')      AS HIGH_RISK_COUNT
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
        GROUP BY INCOME_BAND
        ORDER BY AVG_CHURN_PCT DESC
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_cross_sell() -> pd.DataFrame:
    """Scenario 2 — cross-sell opportunities."""
    return _q(f"""
        SELECT CUSTOMER_ID, NAME, SEGMENT, INCOME_BAND,
               ACTIVE_POLICY_TYPES, ACTIVE_POLICY_TYPE_COUNT,
               LIFETIME_VALUE, UPSELL_PROBABILITY, NBA_ACTION
        FROM {DB}.{GLD}.SCENARIO_2_CROSS_SELL
        ORDER BY LIFETIME_VALUE DESC
    """)


@st.cache_data(ttl=_TTL_AGG, show_spinner=False)
def load_daily_log() -> pd.DataFrame:
    return _q(f"""
        SELECT * FROM {DB}.{GLD}.NBA_DAILY_LOG
        ORDER BY LOG_DATE DESC LIMIT 30
    """)


# ── Live Cortex AI generation ─────────────────────────────────

# mistral-large2 is in legacy state and now returns a 400 from Cortex, which
# silently broke every "Regenerate" button. mistral-large3 is the live model.
CORTEX_MODEL = "mistral-large3"


def generate_nba_message(row: pd.Series) -> str:
    """Generate a personalised outreach message with Cortex COMPLETE.

    Not cached: this is an explicit user-triggered "regenerate" action, and a
    cache would make the button appear broken on a second click.
    """
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
    )
    result = _q(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS MSG",
        [CORTEX_MODEL, prompt],
    )
    return result["MSG"].iloc[0] if not result.empty else "Unable to generate."


def clear_all_caches() -> None:
    """Drop every memoized result. Wire to a button via on_click=clear_all_caches."""
    for fn in (
        load_all_customers_summary, load_customer_360, load_all_360,
        load_nba_message, load_customer_confidence, load_confidence_summary,
        load_cross_sell, load_customer_policies, load_customer_claims,
        load_customer_payments, load_customer_interactions,
        load_customer_transcripts, load_high_value_at_risk,
        load_segment_analytics, load_nba_distribution, load_sentiment_trend,
        load_claim_severity, load_lapses_by_state, load_channel_effectiveness,
        load_income_band_analysis, load_daily_log,
    ):
        fn.clear()
