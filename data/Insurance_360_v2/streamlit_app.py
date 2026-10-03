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

# End-to-end diagram: each lane is (title, subtitle, header colour, nodes);
# each node is (object, detail, [AI / platform features used]).
ARCH_LANES = [
    ("01 Sources", "Raw inputs", "var(--ink)", [
        ("MDB_DATA", "CUSTOMER // POLICY // CLAIM // PAYMENT // INTERACTION "
         "// CALL_TRANSCRIPT", []),
        ("@STAGE_DATA.POLICY_DOCS", "Policy PDF files", ["Stage"]),
        ("Call audio", "Recorded customer calls", []),
    ]),
    ("02 Silver", "AI enrichment", "var(--red)", [
        ("ENRICHED_TRANSCRIPTS", "DT // 1h lag // sentiment, summary, intent, "
         "topics, resolved", ["CORTEX.SENTIMENT", "CORTEX.SUMMARIZE",
                              "AI_CLASSIFY", "CORTEX.COMPLETE"]),
        ("CUSTOMER_VOC_SIGNALS", "DT // recurring themes per customer",
         ["AI_AGG"]),
        ("POLICY_DOCS_STREAM → EXTRACTED_POLICY_DOCS",
         "11 fields per policy", ["Stream", "AI_PARSE_DOCUMENT", "AI_EXTRACT"]),
        ("AUDIO_TRANSCRIPTIONS → ALL_TRANSCRIPTS_UNIFIED",
         "Speech-to-text + text calls", ["AI_TRANSCRIBE"]),
        ("DIM_CUSTOMERS + FACT_*_SIGNALS", "Per-customer feature views", []),
    ]),
    ("03 Gold", "ML + analytics", "var(--yellow)", [
        ("CHURN_SCORES", "XGBoost model // REFRESH_CHURN_SCORES()",
         ["Snowpark ML"]),
        ("CHURN_DEPLOYMENT_VALIDATION + CHURN_MONITOR_VIEW",
         "Post-deploy check + ongoing monitoring", []),
        ("NBA_WITH_CONFIDENCE", "Scenario 10 next best action", []),
        ("CUSTOMER_360_VIEW", "One row per customer // app source", []),
        ("SCENARIO_1..9 views", "Cohort analytics", []),
        ("NBA_DAILY_LOG + URGENT_ALERTS_TODAY", "Daily snapshots", []),
    ]),
    ("04 AI Serving", "Cortex services", "var(--blue)", [
        ("TRANSCRIPT_SEARCH", "Vector + keyword // arctic-embed-m-v1.5",
         ["Cortex Search"]),
        ("CUSTOMER_360_SEMANTIC", "Semantic view // 10 verified queries",
         ["Cortex Analyst", "Semantic Views"]),
        ("INSURANCE_C360_AGENT", "Routes Analyst + Search // evaluated on "
         "30-question set", ["Cortex Agent"]),
        ("mistral-large3", "Outreach scripts, RAG answers, LLM-as-judge",
         ["CORTEX.COMPLETE"]),
    ]),
    ("05 App", "Streamlit // SPCS", "var(--muted)", [
        ("01 Customer 360 // 02 NBA", "Profile + AI outreach + dispatch",
         ["CORTEX.COMPLETE", "Email"]),
        ("03 Segment Analytics", "Scenario views", []),
        ("04 Transcript RAG", "", ["SEARCH_PREVIEW", "CORTEX.COMPLETE"]),
        ("05 Ask Your Data", "Auto-routed across 3 engines",
         ["DATA_AGENT_RUN", "Analyst", "Search"]),
        ("06 Document AI // 07 Ops Monitor", "PDF + audio browser, "
         "model + task health", []),
    ]),
]

ARCH_TASKS = ("TASK_ROOT_NIGHTLY (20:30 UTC) → TASK_SILVER_REFRESH → "
              "TASK_CHURN_SCORING → TASK_NBA_LOG  //  TASK_MORNING_ALERTS "
              "(00:30 UTC)  //  TASK_PROCESS_NEW_PDFS (hourly, when stream "
              "has data)")
ARCH_PLATFORM = ("C360_WH (pipeline) // COMPUTE_WH (app queries) // "
                 "SYSTEM_COMPUTE_POOL_CPU (container) // PYPI_SHARED_REPOSITORY "
                 "// C360_EMAIL_NOTIFY → SYSTEM$SEND_EMAIL")


def _arch_node(name: str, detail: str, feats: list[str]) -> str:
    chips = "".join(
        f'<span style="display:inline-block;margin:4px 4px 0 0;padding:1px 5px;'
        f'background:var(--yellow);border:1.5px solid var(--ink);'
        f'font-family:var(--font-mono);font-size:0.56rem;color:var(--ink)">'
        f'{f}</span>' for f in feats)
    sub = (f'<div style="font-size:0.62rem;color:var(--muted);line-height:1.35;'
           f'margin-top:2px">{detail}</div>') if detail else ""
    return (f'<div style="background:var(--white);border:2px solid var(--ink);'
            f'box-shadow:var(--drop-3);padding:7px 8px;margin-bottom:9px">'
            f'<div style="font-family:var(--font-mono);font-size:0.64rem;'
            f'font-weight:700;color:var(--ink);word-break:break-word">{name}'
            f'</div>{sub}{chips}</div>')


def _arch_lane(title: str, sub: str, colour: str, nodes: list) -> str:
    fg = "var(--ink)" if colour == "var(--yellow)" else "var(--white)"
    return (f'<div style="flex:1 1 0;min-width:150px">'
            f'<div style="background:{colour};color:{fg};border:2px solid '
            f'var(--ink);padding:6px 8px;margin-bottom:9px;font-family:'
            f'var(--font-display);font-size:0.74rem;text-transform:uppercase">'
            f'{title}<div style="font-family:var(--font-body);font-size:0.6rem;'
            f'text-transform:none;opacity:0.85">{sub}</div></div>'
            + "".join(_arch_node(*n) for n in nodes) + "</div>")


_arrow = ('<div style="flex:0 0 18px;align-self:center;text-align:center;'
          'font-family:var(--font-display);font-size:1.2rem;color:var(--ink)">'
          '→</div>')
_band = ('<div style="margin-top:6px;border:2px solid var(--ink);padding:7px '
         '9px;background:var(--container);font-size:0.64rem;color:var(--ink)">'
         '<b style="font-family:var(--font-display);text-transform:uppercase;'
         'margin-right:8px">{}</b><span style="font-family:var(--font-mono)">'
         '{}</span></div>')

st.html('<div class="bh-box paper"><div style="display:flex;gap:6px;'
        'overflow-x:auto;align-items:flex-start">'
        + _arrow.join(_arch_lane(*lane) for lane in ARCH_LANES) + '</div>'
        + _band.format("Orchestration", ARCH_TASKS)
        + _band.format("Platform", ARCH_PLATFORM) + '</div>')

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
