"""
streamlit_app.py -- COMMAND CENTER   (Insurance_360_v2, Bauhaus edition)

Entry point. The "Command Center" nav item in the Stitch mockups had no screen
of its own, so this is composed from the shared design language: eyebrow +
oversized banner, live KPI bento, module entry grid, pipeline architecture
block.

Unlike the other pages this one runs a single cheap aggregate rather than
pulling the full 1,000-row frame, so the landing screen paints fast.
"""
import os
import sys
import time

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(__file__))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import DB, GLD, clear_all_caches, run_query  # noqa: E402
from utils.theme import (  # noqa: E402
    INK, MUTED, RED, YELLOW, apply_theme, banner, bento, inr, kpi, loading,
    section, sidebar, topbar,
)

st.set_page_config(page_title="Command Center // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

banner(
    "Command Center",
    "Unified policyholder intelligence &mdash; structured signals fused with "
    "AI-enriched call transcripts, XGBoost churn scoring, Scenario 10 "
    "next-best-action logic and Cortex-generated outreach. "
    "<b>17 Snowflake AI/ML features</b> in one pipeline.",
    eyebrow="System Online // Insurance_C360",
)


@st.cache_data(ttl=1800, show_spinner=False)
def load_headline() -> pd.Series:
    """One cheap aggregate for the landing KPIs - avoids the 1,000-row pull."""
    df = run_query(f"""
        SELECT
          COUNT(*)                                  AS CUSTOMERS,
          COUNT_IF(NBA_PRIORITY = 'Urgent')         AS URGENT,
          COUNT_IF(CHURN_RISK_LABEL = 'High')       AS HIGH_RISK,
          SUM(CASE WHEN CHURN_RISK_LABEL = 'High'
                   THEN LIFETIME_VALUE ELSE 0 END)  AS LTV_AT_RISK,
          ROUND(AVG(CHURN_RISK_SCORE) * 100, 1)     AS AVG_CHURN_PCT,
          ROUND(AVG(AVG_SENTIMENT_SCORE), 3)        AS AVG_SENTIMENT,
          SUM(TOTAL_CALLS)                          AS CALLS
        FROM {DB}.{GLD}.CUSTOMER_360_VIEW
    """)
    return df.iloc[0]


_t0 = time.perf_counter()
with loading("Polling engine state"):
    h = load_headline()
_ms = int((time.perf_counter() - _t0) * 1000)

customers = int(h["CUSTOMERS"] or 0)
urgent = int(h["URGENT"] or 0)
high_risk = int(h["HIGH_RISK"] or 0)

topbar(records=f"{customers:,}", latency=f"{_ms} ms")

bento([
    kpi("Policyholders", f"{customers:,}", "Scored every refresh",
        icon="◼", bar_pct=100, bar_color=INK),
    kpi("Urgent Triage", f"{urgent:,}", "Awaiting intervention", tone="red",
        icon="▲", bar_pct=int(urgent / customers * 100) if customers else 0,
        bar_color=RED),
    kpi("High Churn Risk", f"{high_risk:,}", "Model-flagged cohort",
        tone="yellow", icon="◤",
        bar_pct=int(high_risk / customers * 100) if customers else 0,
        bar_color=INK),
    kpi("LTV At Risk", inr(h["LTV_AT_RISK"], compact=True),
        "Exposure in high-risk cohort", tone="dark", icon="₹"),
    kpi("Avg Churn Score", f"{float(h['AVG_CHURN_PCT'] or 0):.1f}%",
        "Portfolio mean", tone="paper", icon="◈",
        bar_pct=int(float(h["AVG_CHURN_PCT"] or 0)), bar_color=MUTED),
    kpi("Voice Signal", f"{float(h['AVG_SENTIMENT'] or 0):+.3f}",
        f"{int(h['CALLS'] or 0):,} calls analysed", tone="blue", icon="◉"),
])

# ── Module entry grid ─────────────────────────────────────────
section("Modules", "01")

MODULES = [
    ("pages/1_Customer_360.py", "01", "Customer 360", "Full Profile",
     "Policies, claims, payments, sentiment, churn score, NBA + AI outreach script.",
     ""),
    ("pages/2_NBA_Dashboard.py", "02", "NBA Priority", "Execution Queue",
     "Scenario 10 triage across every policyholder with dispatch channel and SLA tier.",
     "yellow"),
    ("pages/3_Segment_Analytics.py", "03", "Segment Analytics", "Cohort Scenarios",
     "Churn and LTV by segment, claim severity, lapses by state, channel friction.",
     "paper"),
    ("pages/4_Transcript_Explorer.py", "04", "Transcript RAG", "Cortex Search",
     "Semantic retrieval over 866 call transcripts with grounded AI synthesis.",
     ""),
    ("pages/5_Ask_Your_Data.py", "05", "Ask Your Data", "Three Engines",
     "Cortex Agent, Analyst text-to-SQL and Search, auto-routed per question.",
     "blue"),
    ("pages/6_Document_AI.py", "06", "Document AI", "PDF + Audio",
     "AI_PARSE_DOCUMENT, AI_EXTRACT and AI_TRANSCRIBE over policy files and calls.",
     "red"),
    ("pages/7_Ops_Monitor.py", "07", "Ops Monitor", "Pipeline Health",
     "Task history, model validation, NBA daily trends, confidence distribution.",
     "dark"),
]

st.html('<div class="bh-bento">' + "".join(
    f'<div class="bh-kpi {tone}">'
    f'<div class="bh-kpi-top"><span class="bh-kpi-k">{num} // {label}</span></div>'
    f'<div class="bh-kpi-v" style="font-size:clamp(1.1rem,1.9vw,1.5rem);'
    f'margin:10px 0 6px 0">{head}</div>'
    f'<div class="bh-kpi-s" style="font-family:var(--font-body);'
    f'text-transform:none;letter-spacing:0;font-weight:500;font-size:0.76rem;'
    f'line-height:1.45">{body}</div></div>'
    for _p, num, label, head, body, tone in MODULES
) + "</div>")

nav_cols = st.columns(3)
for i, (path, num, label, _h, _b, _t) in enumerate(MODULES):
    with nav_cols[i % 3]:
        st.page_link(path, label=f"{num}  Open {label}",
                     use_container_width=True)

# ── Pipeline architecture ─────────────────────────────────────
section("Pipeline Architecture", "02")

LAYERS = [
    ("Bronze", "MDB_DATA", INK,
     "6 source tables // 1,000 customers // 1,642 policies // 866 transcripts"),
    ("Silver", "Cortex AI", RED,
     "Dynamic Tables: SENTIMENT, SUMMARIZE, AI_CLASSIFY, AI_AGG, AI_TRANSCRIBE"),
    ("Gold", "Analytics", YELLOW,
     "Customer 360 + XGBoost churn scores + NBA engine + AI outreach messages"),
    ("App", "Serving", MUTED,
     "Semantic View (10 VQRs) + Cortex Agent + Cortex Search + Streamlit (7 screens)"),
]

st.html('<div class="bh-box paper">' + "".join(
    f'<div class="bh-kv" style="align-items:center">'
    f'<span class="bh-kv-k" style="display:flex;align-items:center;gap:10px">'
    f'<span style="width:13px;height:13px;background:{colour};'
    f'border:2px solid var(--ink);display:inline-block"></span>'
    f'<b style="font-family:var(--font-display);font-size:0.8rem;'
    f'color:var(--ink)">{tier}</b>'
    f'<span style="color:var(--muted)">{name}</span></span>'
    f'<span class="bh-kv-v" style="font-weight:600;font-size:0.68rem;'
    f'color:var(--muted);text-align:right">{detail}</span></div>'
    for tier, name, colour, detail in LAYERS
) + "</div>")

st.html(
    '<div class="bh-box dark tight"><div class="bh-box-title">'
    '<span>Feature Inventory</span><span>17 / 17</span></div>'
    '<div style="display:flex;flex-wrap:wrap;gap:0">' + "".join(
        f'<span class="bh-chip" style="background:var(--yellow);'
        f'color:var(--ink);border-color:var(--paper)">{f}</span>'
        for f in [
            "CORTEX.SENTIMENT", "CORTEX.SUMMARIZE", "CORTEX.COMPLETE",
            "AI_CLASSIFY", "AI_AGG", "AI_EXTRACT", "AI_PARSE_DOCUMENT",
            "AI_TRANSCRIBE", "Cortex Search", "Cortex Analyst", "Cortex Agent",
            "Snowpark ML", "Semantic Views", "Dynamic Tables",
            "MCP Server", "Email Notifications", "Web Search",
        ]) + '</div></div>')

st.caption(f"{DB} // built entirely with Cortex Code // "
           "Bauhaus neo-brutalist edition")

with st.sidebar:
    st.button("Sync Snowflake", on_click=clear_all_caches,
              use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
