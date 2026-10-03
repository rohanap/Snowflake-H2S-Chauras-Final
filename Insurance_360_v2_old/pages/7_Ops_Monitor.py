"""
Page 7 -- OPS MONITOR   (Bauhaus / Neo-Brutalist)
Operational intelligence: task pipeline status, model validation metrics,
NBA daily log trends, churn model drift monitoring, and confidence
distribution. Proves the system is production-ready, not just a demo.
"""
import os
import sys
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import DB, GLD, clear_all_caches, run_query  # noqa: E402
from utils.theme import (  # noqa: E402
    BLUE, BRIGHT, CONTAINER_TOP, INK, MUTED, PAPER, RED, YELLOW, apply_theme,
    banner, bento, inr, kpi, loading, section, sidebar, topbar,
)

st.set_page_config(page_title="Ops Monitor // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=BRIGHT,
    font=dict(family="Inter, system-ui, sans-serif", color=INK, size=12),
    margin=dict(t=44, b=34, l=54, r=18), showlegend=False, bargap=0.28,
)
AXIS = dict(gridcolor=CONTAINER_TOP, linecolor=INK, linewidth=2,
            zerolinecolor=INK, ticks="outside", tickcolor=INK)
OUTLINE = dict(line=dict(color=INK, width=2))

banner(
    "Ops Monitor",
    "Pipeline health, model validation metrics, NBA daily trends and drift "
    "monitoring. Proof that the system runs autonomously &mdash; not just a demo.",
    eyebrow="Production Readiness // Guardrails",
)

_q = run_query


@st.cache_data(ttl=900, show_spinner=False)
def load_model_validation() -> pd.DataFrame:
    return _q("""
        SELECT
          SPLIT,
          COUNT(*) AS TOTAL,
          COUNT_IF(CORRECT = 1) AS CORRECT_CT,
          COUNT_IF(CORRECT = 0) AS WRONG_CT,
          ROUND(COUNT_IF(CORRECT = 1)::FLOAT / COUNT(*) * 100, 1) AS ACCURACY_PCT,
          COUNT_IF(CHURN_PRED = 1 AND HAS_CHURNED = 1) AS TP,
          COUNT_IF(CHURN_PRED = 1 AND HAS_CHURNED = 0) AS FP,
          COUNT_IF(CHURN_PRED = 0 AND HAS_CHURNED = 1) AS FN,
          COUNT_IF(CHURN_PRED = 0 AND HAS_CHURNED = 0) AS TN
        FROM INSURANCE_C360.GOLD.CHURN_DEPLOYMENT_VALIDATION
        GROUP BY SPLIT
    """)


@st.cache_data(ttl=900, show_spinner=False)
def load_nba_log() -> pd.DataFrame:
    return _q(f"""
        SELECT * FROM {DB}.{GLD}.NBA_DAILY_LOG
        ORDER BY LOG_DATE DESC LIMIT 30
    """)


@st.cache_data(ttl=900, show_spinner=False)
def load_churn_distribution() -> pd.DataFrame:
    return _q(f"""
        SELECT CHURN_RISK_LABEL, COUNT(*) AS CT,
               ROUND(AVG(CHURN_RISK_SCORE) * 100, 1) AS AVG_SCORE
        FROM {DB}.{GLD}.CHURN_SCORES
        GROUP BY CHURN_RISK_LABEL
    """)


@st.cache_data(ttl=900, show_spinner=False)
def load_confidence_dist() -> pd.DataFrame:
    return _q(f"""
        SELECT
          CASE WHEN NBA_CONFIDENCE >= 0.75 THEN 'Strong (>=75%)'
               WHEN NBA_CONFIDENCE >= 0.50 THEN 'Moderate (50-74%)'
               WHEN NBA_CONFIDENCE >= 0.25 THEN 'Weak (25-49%)'
               ELSE 'Low (<25%)' END AS BAND,
          COUNT(*) AS CT,
          ROUND(AVG(NBA_CONFIDENCE) * 100, 1) AS AVG_CONF
        FROM {DB}.{GLD}.NBA_WITH_CONFIDENCE
        GROUP BY 1 ORDER BY AVG_CONF DESC
    """)


@st.cache_data(ttl=900, show_spinner=False)
def load_task_status() -> pd.DataFrame:
    return _q("""
        SELECT NAME, STATE, SCHEDULE, COMMENT
        FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
    """)


@st.cache_data(ttl=900, show_spinner=False)
def load_alert_status() -> pd.DataFrame:
    return _q("""
        SELECT NAME, STATE, SCHEDULE, CONDITION
        FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
    """)


# ── Load data ────────────────────────────────────────────────
_t0 = time.perf_counter()
with loading("Loading ops metrics"):
    val = load_model_validation()
    nba_log = load_nba_log()
    churn_dist = load_churn_distribution()
    conf_dist = load_confidence_dist()
_ms = int((time.perf_counter() - _t0) * 1000)

topbar(records="ops", latency=f"{_ms} ms", schema="GOLD")

# ── Model Validation KPIs ────────────────────────────────────
test = val[val["SPLIT"] == "TEST"]
train = val[val["SPLIT"] == "TRAIN"]

if not test.empty:
    t = test.iloc[0]
    precision = round(t["TP"] / max(1, t["TP"] + t["FP"]) * 100, 1)
    recall = round(t["TP"] / max(1, t["TP"] + t["FN"]) * 100, 1)
    f1 = round(2 * precision * recall / max(1, precision + recall), 1)
    bento([
        kpi("Test Accuracy", f"{float(t['ACCURACY_PCT'])}%",
            f"{int(t['CORRECT_CT'])}/{int(t['TOTAL'])} correct",
            tone="yellow" if t["ACCURACY_PCT"] >= 75 else "red", icon="◼",
            bar_pct=int(t["ACCURACY_PCT"]), bar_color=INK),
        kpi("Precision", f"{precision}%",
            f"{int(t['TP'])} TP / {int(t['FP'])} FP", icon="◤",
            bar_pct=int(precision), bar_color=YELLOW),
        kpi("Recall", f"{recall}%",
            f"{int(t['TP'])} TP / {int(t['FN'])} FN", icon="▲",
            bar_pct=int(recall), bar_color=YELLOW),
        kpi("F1 Score", f"{f1}%",
            "Harmonic mean", tone="dark", icon="◈",
            bar_pct=int(f1), bar_color=INK),
        kpi("Train Accuracy", f"{float(train.iloc[0]['ACCURACY_PCT'])}%",
            f"{int(train.iloc[0]['TOTAL'])} samples", tone="paper", icon="●",
            bar_pct=int(train.iloc[0]["ACCURACY_PCT"]),
            bar_color=MUTED) if not train.empty else
        kpi("Train", "N/A", "", tone="paper", icon="●"),
    ])

# ── Confusion Matrix ─────────────────────────────────────────
section("Model Validation // Confusion Matrix", "01")

if not test.empty:
    t = test.iloc[0]
    cm = [[int(t["TN"]), int(t["FP"])], [int(t["FN"]), int(t["TP"])]]

    c1, c2 = st.columns([1, 1])
    with c1:
        st.html(f"""
        <div class="bh-box">
            <div class="bh-box-title"><span>Test Set Confusion Matrix</span>
                <span>{int(t['TOTAL'])} samples</span></div>
            <table class="bh-ledger" style="text-align:center">
                <tr><th></th><th>Predicted: Retained</th><th>Predicted: Churned</th></tr>
                <tr><td><b>Actual: Retained</b></td>
                    <td style="background:var(--bright);font-weight:700">{cm[0][0]} TN</td>
                    <td style="background:{RED}20;font-weight:700;color:{RED}">{cm[0][1]} FP</td></tr>
                <tr><td><b>Actual: Churned</b></td>
                    <td style="background:{RED}20;font-weight:700;color:{RED}">{cm[1][0]} FN</td>
                    <td style="background:{YELLOW}40;font-weight:700">{cm[1][1]} TP</td></tr>
            </table>
        </div>""")

    with c2:
        rows = [
            ("True Positives", int(t["TP"]), "Correctly predicted churn"),
            ("True Negatives", int(t["TN"]), "Correctly predicted retained"),
            ("False Positives", int(t["FP"]), "Wrongly flagged as churn"),
            ("False Negatives", int(t["FN"]), "Missed actual churn"),
        ]
        kvs = "".join(
            f'<div class="bh-kv"><span class="bh-kv-k">{k}</span>'
            f'<span class="bh-kv-v">{v} <span style="color:var(--muted);'
            f'font-size:0.65rem;font-weight:500">{d}</span></span></div>'
            for k, v, d in rows)
        st.html(f'<div class="bh-box paper"><div class="bh-box-title">'
                f'<span>Classification Metrics</span><span>XGB_V3</span></div>'
                f'{kvs}</div>')
else:
    st.info("No model validation data available.")

# ── Churn Score Distribution ─────────────────────────────────
section("Churn Score Distribution", "02")

if not churn_dist.empty:
    mx = float(churn_dist["CT"].max()) or 1.0
    cols = {"High": RED, "Medium": YELLOW, "Low": INK}
    bars = "".join(
        f'<div><div class="bh-bar-l"><span>{r["CHURN_RISK_LABEL"]}'
        f' ({r["AVG_SCORE"]}% avg)</span>'
        f'<span>{int(r["CT"]):,}</span></div>'
        f'<div class="bh-bar-t"><i style="width:{max(2, int(r["CT"] / mx * 100))}%;'
        f'background:{cols.get(r["CHURN_RISK_LABEL"], INK)}"></i></div></div>'
        for _, r in churn_dist.iterrows())
    st.html(f'<div class="bh-box"><div class="bh-box-title">'
            f'<span>Current Model Output</span><span>CHURN_SCORES</span></div>'
            f'<div class="bh-bars">{bars}</div></div>')

# ── NBA Confidence Distribution ──────────────────────────────
section("NBA Confidence Distribution", "03")

if not conf_dist.empty:
    mx = float(conf_dist["CT"].max()) or 1.0
    band_cols = {"Strong (>=75%)": YELLOW, "Moderate (50-74%)": INK,
                 "Weak (25-49%)": MUTED, "Low (<25%)": RED}
    bars = "".join(
        f'<div><div class="bh-bar-l"><span>{r["BAND"]}</span>'
        f'<span>{int(r["CT"]):,}</span></div>'
        f'<div class="bh-bar-t"><i style="width:{max(2, int(r["CT"] / mx * 100))}%;'
        f'background:{band_cols.get(r["BAND"], INK)}"></i></div></div>'
        for _, r in conf_dist.iterrows())
    st.html(f'<div class="bh-box"><div class="bh-box-title">'
            f'<span>NBA_WITH_CONFIDENCE</span>'
            f'<span>Multi-Signal Convergence</span></div>'
            f'<div class="bh-bars">{bars}</div></div>')

# ── NBA Daily Log Trend ──────────────────────────────────────
section("NBA Daily Log Trend", "04")

if nba_log.empty:
    st.info("No daily log entries yet.")
else:
    log = nba_log.copy()
    log["LOG_DATE"] = pd.to_datetime(log["LOG_DATE"])
    log = log.sort_values("LOG_DATE")
    log = log.drop_duplicates(subset=["LOG_DATE"], keep="last")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=log["LOG_DATE"], y=log["URGENT_COUNT"],
                         name="Urgent", marker=dict(color=RED, **OUTLINE)))
    fig.add_trace(go.Bar(x=log["LOG_DATE"], y=log["HIGH_COUNT"],
                         name="High", marker=dict(color=INK, **OUTLINE)))
    fig.add_trace(go.Bar(x=log["LOG_DATE"], y=log["MEDIUM_COUNT"],
                         name="Medium", marker=dict(color=YELLOW, **OUTLINE)))
    fig.add_trace(go.Bar(x=log["LOG_DATE"], y=log["LOW_COUNT"],
                         name="Low", marker=dict(color=MUTED, **OUTLINE)))
    fig.update_layout(**{**PLOT, "barmode": "stack", "showlegend": True,
                         "margin": dict(t=56, b=34, l=54, r=18),
                         "legend": dict(bgcolor=BRIGHT, bordercolor=INK,
                                        borderwidth=2, orientation="h",
                                        y=1.08, x=0.5, xanchor="center")})
    fig.update_xaxes(**AXIS)
    fig.update_yaxes(title="CUSTOMERS", **AXIS)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        kvs = "".join(
            f'<div class="bh-kv"><span class="bh-kv-k">{k}</span>'
            f'<span class="bh-kv-v">{v}</span></div>'
            for k, v in [
                ("Latest Log Date", str(log["LOG_DATE"].max())[:10]),
                ("Avg Churn Risk", f"{float(log['AVG_CHURN_RISK'].mean()):.4f}"),
                ("LTV At Risk (latest)", inr(log.iloc[-1]["LTV_AT_RISK"])),
                ("Log Entries", f"{len(log)}"),
            ])
        st.html(f'<div class="bh-box paper"><div class="bh-box-title">'
                f'<span>Log Summary</span><span>NBA_DAILY_LOG</span></div>'
                f'{kvs}</div>')
    with c2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=log["LOG_DATE"], y=log["AVG_CHURN_RISK"],
            mode="lines+markers", line=dict(color=INK, width=3),
            marker=dict(size=9, color=YELLOW, line=dict(color=INK, width=2))))
        fig2.add_hline(y=0.05, line_dash="dot", line_color=RED, line_width=2,
                       annotation_text="DRIFT LOW (5%)",
                       annotation_font=dict(family="Space Grotesk", color=RED, size=10))
        fig2.add_hline(y=0.60, line_dash="dot", line_color=RED, line_width=2,
                       annotation_text="DRIFT HIGH (60%)",
                       annotation_font=dict(family="Space Grotesk", color=RED, size=10))
        fig2.update_layout(**PLOT)
        fig2.update_layout(title=dict(text="AVG CHURN RISK OVER TIME",
                                      font=dict(family="Space Grotesk", size=14, color=INK)))
        fig2.update_xaxes(**AXIS)
        fig2.update_yaxes(title="AVG RISK", range=[0, 1], **AXIS)
        st.plotly_chart(fig2, use_container_width=True)

# ── Task Pipeline Status ─────────────────────────────────────
section("Task Pipeline Status", "05")

TASKS = [
    ("TASK_ROOT_NIGHTLY", "CRON 20:30 UTC daily", "Root — triggers nightly pipeline"),
    ("TASK_SILVER_REFRESH", "After ROOT", "Force-refresh Silver Dynamic Tables"),
    ("TASK_CHURN_SCORING", "After SILVER", "Re-score all customers via ML model"),
    ("TASK_NBA_LOG", "After SCORING", "Append daily NBA summary to log table"),
    ("TASK_MORNING_ALERTS", "CRON 00:30 UTC", "Snapshot Urgent/High NBA for push"),
    ("TASK_PROCESS_NEW_PDFS", "60 MIN (stream)", "Auto-process new PDFs via AI_PARSE + AI_EXTRACT"),
]

rows = "".join(
    f'<tr><td><b>{name}</b></td><td>{sched}</td><td>{desc}</td></tr>'
    for name, sched, desc in TASKS)
st.html(f"""
<table class="bh-ledger">
    <tr><th>Task</th><th>Schedule</th><th>Description</th></tr>
    {rows}
</table>""")

st.html("""
<div class="bh-box dark tight"><div class="bh-box-title">
    <span>Drift Alert</span><span>ALERT_CHURN_MODEL_DRIFT</span></div>
    <div class="bh-kv"><span class="bh-kv-k">Schedule</span>
        <span class="bh-kv-v">CRON 0 8 * * * UTC</span></div>
    <div class="bh-kv"><span class="bh-kv-k">Condition</span>
        <span class="bh-kv-v">High-risk % &lt; 5% OR &gt; 60%</span></div>
    <div class="bh-kv"><span class="bh-kv-k">Action</span>
        <span class="bh-kv-v">Insert sentinel row into NBA_DAILY_LOG</span></div>
</div>""")

# ── Architecture ─────────────────────────────────────────────
section("Pipeline Architecture", "06")

st.html(
    '<div class="bh-box paper"><div class="bh-box-title">'
    '<span>Medallion Pipeline</span><span>17 AI/ML Features</span></div>'
    '<div style="font-family:var(--font-mono);font-size:0.68rem;'
    'font-weight:700;letter-spacing:0.06em;line-height:2.2;'
    'color:var(--ink);white-space:pre-wrap">'
    'MDB_DATA (6 tables) → SILVER (DTs: ENRICHED_TRANSCRIPTS, CUSTOMER_VOC_SIGNALS)\n'
    '                     → SILVER (AI: SENTIMENT, SUMMARIZE, AI_CLASSIFY, AI_AGG)\n'
    '                     → SILVER (Docs: AI_PARSE_DOCUMENT, AI_EXTRACT, AI_TRANSCRIBE)\n'
    '                     → GOLD (CUSTOMER_360_VIEW + XGBoost + NBA Engine)\n'
    '                     → APP (Semantic View + Cortex Agent + Cortex Search + Streamlit)</div>'
    '</div>')

st.caption("INSURANCE_C360 // built entirely with Cortex Code")

with st.sidebar:
    st.button("Sync Snowflake", on_click=clear_all_caches,
              use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
