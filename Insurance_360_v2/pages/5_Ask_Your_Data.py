"""
Page 5 -- ASK YOUR DATA   (Bauhaus / Neo-Brutalist)
Built from stitch_snowflake_streamlit_ui_redesign/ask_your_data/

Three engines behind one input: Cortex Agent (orchestrated), Cortex Analyst
(text-to-SQL over the semantic view) and Cortex Search (RAG over transcripts).

Analyst and the Agent object both need the in-app REST bridge (`_snowflake`).
When that module is missing from the runtime, those modes are removed from the
selector and Auto falls back to Search, so the page always works.

History stores only serialisable primitives; charts are rebuilt from the cached
SQL result on demand rather than pickled into session_state.
"""
import os
import sys
import time

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import clear_all_caches, run_query  # noqa: E402
from utils.rag_agent import (  # noqa: E402
    api_available, api_unavailable_reason, ask_agent,
)
from utils.theme import (  # noqa: E402
    BLUE, BRIGHT, CONTAINER_TOP, INK, MUTED, RED, YELLOW, apply_theme, banner,
    loading, section, sidebar, topbar,
)

st.set_page_config(page_title="Ask Your Data // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

banner(
    "Ask Your Data",
    "One input, three engines. <b>Metrics</b> route to Cortex Analyst "
    "(text-to-SQL over the semantic view). <b>Calls and transcripts</b> route to "
    "Cortex Search. <b>Cortex Agent</b> orchestrates both tools automatically.",
    eyebrow="Natural Language Interface // Auto-Routed",
)

MODE_META = {
    "agent": ("Cortex Agent // Orchestrated", BLUE),
    "analyst": ("Cortex Analyst // Text-To-SQL", INK),
    "search": ("Cortex Search // RAG", RED),
}
MODE_MAP = {"Auto": None, "Cortex Agent": "agent",
            "Cortex Analyst": "analyst", "Cortex Search": "search"}

ANALYST_QS = [
    "How many high risk customers are there?",
    "What is the average lifetime value by segment?",
    "Which state has the highest average churn risk?",
    "Total LTV at risk from high churn customers?",
    "How many customers are in each NBA priority?",
    "Average sentiment score by income band?",
]
SEARCH_QS = [
    "customers who want to cancel their policy",
    "calls about rejected or delayed insurance claims",
    "customers asking about premium or renewal",
    "complaints about service quality or wait times",
    "customers interested in adding life cover",
]

st.session_state.setdefault("a5_history", [])
st.session_state.setdefault("a5_pending", None)


@st.cache_data(ttl=900, max_entries=50, show_spinner=False)
def run_generated_sql(sql: str) -> pd.DataFrame:
    """Execute Analyst/Agent-generated SQL, memoized per statement."""
    return run_query(sql)


def _chart(df: pd.DataFrame, hint: str):
    num = df.select_dtypes(include="number").columns.tolist()
    cat = df.select_dtypes(exclude="number").columns.tolist()
    if len(df) <= 1 or not num or not cat:
        return None
    x, y = cat[0], num[0]
    if hint == "line" and len(df) > 2:
        fig = px.line(df, x=x, y=y, markers=True,
                      color_discrete_sequence=[INK])
        fig.update_traces(line=dict(width=3),
                          marker=dict(size=9, color=YELLOW,
                                      line=dict(color=INK, width=2)))
    elif hint == "pie" and len(df) <= 8:
        fig = px.pie(df, names=x, values=y,
                     color_discrete_sequence=[INK, YELLOW, RED, BLUE, MUTED])
        fig.update_traces(marker=dict(line=dict(color=INK, width=2)),
                          textfont=dict(family="Space Grotesk", size=13))
    else:
        fig = px.bar(df, x=x, y=y, color_discrete_sequence=[YELLOW],
                     text_auto=".3s")
        fig.update_traces(marker=dict(line=dict(color=INK, width=2)),
                          textfont=dict(family="Space Grotesk", size=12,
                                        color=INK))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=BRIGHT,
        font=dict(family="Inter, system-ui, sans-serif", color=INK, size=12),
        margin=dict(t=28, b=32, l=52, r=16),
        showlegend=(hint == "pie"), bargap=0.28)
    fig.update_xaxes(gridcolor=CONTAINER_TOP, linecolor=INK, linewidth=2,
                     ticks="outside", tickcolor=INK)
    fig.update_yaxes(gridcolor=CONTAINER_TOP, linecolor=INK, linewidth=2,
                     ticks="outside", tickcolor=INK)
    return fig


def _engine_strip(mode: str, confidence: float) -> None:
    label, clr = MODE_META.get(mode, MODE_META["search"])
    st.html(
        f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;'
        f'background:{clr};border:3px solid {INK};padding:7px 13px;'
        f'box-shadow:3px 3px 0 0 {INK};margin-bottom:12px">'
        f'<span style="font-family:var(--font-mono);font-size:0.62rem;'
        f'font-weight:700;letter-spacing:0.12em;text-transform:uppercase;'
        f'color:{"#f5f0e8" if clr in (INK, RED, BLUE) else INK}">{label}</span>'
        f'<span style="font-family:var(--font-mono);font-size:0.62rem;'
        f'font-weight:700;letter-spacing:0.08em;margin-left:auto;'
        f'color:{"#f5f0e8" if clr in (INK, RED, BLUE) else INK}">'
        f'Confidence {confidence:.0%}</span></div>')


def _search_cards(rows: list, limit: int) -> None:
    cards = []
    for r in rows[:limit]:
        s = float(r.get("SENTIMENT_SCORE") or 0)
        tone = "red" if s < -0.3 else "yellow" if s < 0.1 else "ghost"
        cards.append(f"""
        <div class="bh-box tight" style="margin-bottom:12px">
            <div class="bh-box-title">
                <span>{r.get('CUSTOMER_NAME') or ''}</span>
                <span style="color:{RED if s < -0.3 else INK}">{round(s, 2)}</span>
            </div>
            <div style="margin-bottom:8px">
                <span class="bh-chip {tone}">{str(r.get('CUSTOMER_INTENT') or '').replace('_', ' ').title()}</span>
                <span class="bh-chip ghost">{str(r.get('INTERACTION_DATE') or '')[:10]}</span>
                <span class="bh-chip ghost">{r.get('CHANNEL') or ''}</span>
            </div>
            <div style="font-family:var(--font-body);font-size:0.84rem;
                        line-height:1.6;color:var(--muted)">
                {r.get('CALL_SUMMARY') or ''}</div>
        </div>""")
    if cards:
        st.html("".join(cards))


def _render(msg: dict, result_limit: int) -> None:
    """Render one assistant turn from primitives only."""
    mode = msg.get("mode", "search")
    _engine_strip(mode, msg.get("confidence", 0))

    if msg.get("error"):
        st.error(f"Engine error: {msg['error']}")

    answer = msg.get("answer") or ""
    if answer:
        if mode == "analyst":
            st.markdown(answer)
        else:
            st.html('<div class="bh-box tight"><div class="bh-box-title">'
                    f'<span>{"Agent Response" if mode == "agent" else "RAG Synthesis"}'
                    '</span></div>'
                    f'<div style="font-family:var(--font-body);font-size:0.88rem;'
                    f'line-height:1.7;color:var(--ink)">{answer}</div></div>')

    sql_text = msg.get("sql") or ""
    if sql_text:
        with st.expander("Generated SQL"):
            st.code(sql_text, language="sql")
        try:
            df = run_generated_sql(sql_text)
        except Exception as e:
            st.error(f"SQL execution error: {e}")
        else:
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
                fig = _chart(df, msg.get("chart_hint", "bar"))
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True,
                                    key=f"a5_chart_{msg['turn']}")

    if msg.get("results"):
        st.caption(f"{len(msg['results'])} matching transcripts")
        _search_cards(msg["results"], result_limit)


# ── Controls ──────────────────────────────────────────────────
section("Engine Selection", "01")

m1, m2 = st.columns([3, 1])
with m1:
    _modes = list(MODE_MAP.keys()) if api_available() else ["Auto", "Cortex Search"]
    force = st.segmented_control("Mode", _modes, default=_modes[0],
                                 key="a5_mode",
                                 label_visibility="collapsed") or _modes[0]
with m2:
    if st.button("Clear Session", key="a5_clear", use_container_width=True,
                 disabled=not st.session_state["a5_history"]):
        st.session_state["a5_history"] = []
        st.rerun()

if not api_available():
    st.warning("**Cortex Search only in this runtime.** " + api_unavailable_reason())

topbar(records=f"{len(st.session_state['a5_history']) // 2} turns",
       latency="live", schema="GOLD")

# ── Example probes ────────────────────────────────────────────
section("Example Probes", "02")
ea, es = st.tabs(["Metrics // Analyst", "Transcripts // Search"])
with ea:
    if not api_available():
        st.caption("Analyst unavailable here — these route to Search instead")
    cols = st.columns(3)
    for i, q in enumerate(ANALYST_QS):
        if cols[i % 3].button(q, key=f"a5_aq_{i}", use_container_width=True):
            st.session_state["a5_pending"] = q
            st.rerun()
with es:
    cols = st.columns(3)
    for i, q in enumerate(SEARCH_QS):
        if cols[i % 3].button(q, key=f"a5_sq_{i}", use_container_width=True):
            st.session_state["a5_pending"] = q
            st.rerun()

# ── Conversation ──────────────────────────────────────────────
section("Conversation", "03")

if not st.session_state["a5_history"]:
    st.html('<div class="bh-box paper"><div class="bh-box-title">'
            '<span>No Session Yet</span><span>Idle</span></div>'
            '<div style="font-family:var(--font-body);font-size:0.88rem;'
            'color:var(--muted)">Ask a question below, or fire one of the '
            'example probes. Metric questions route to text-to-SQL; call and '
            'transcript questions route to vector search.</div></div>')

for msg in st.session_state["a5_history"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.html('<div style="font-family:var(--font-display);'
                    'font-weight:700;font-size:0.95rem;text-transform:uppercase;'
                    f'letter-spacing:-0.01em;color:var(--ink)">{msg["text"]}</div>')
        else:
            _render(msg, result_limit=3)

typed = st.chat_input("Query the policyholder book…")
question = typed or st.session_state.pop("a5_pending", None)

if question and question.strip():
    question = question.strip()
    turn = len(st.session_state["a5_history"])
    st.session_state["a5_history"].append(
        {"role": "user", "text": question, "turn": turn})
    with st.chat_message("user"):
        st.html('<div style="font-family:var(--font-display);font-weight:700;'
                'font-size:0.95rem;text-transform:uppercase;'
                f'letter-spacing:-0.01em;color:var(--ink)">{question}</div>')

    with st.chat_message("assistant"):
        _t0 = time.perf_counter()
        with loading("Routing and executing"):
            resp = ask_agent(question,
                             history=st.session_state["a5_history"][:-1],
                             force_mode=MODE_MAP.get(force))
        _ms = int((time.perf_counter() - _t0) * 1000)

        if resp.get("confidence", 0) < 0.5 and not resp.get("error"):
            st.warning("Low confidence — try rephrasing or forcing a mode.")

        entry = {
            "role": "assistant", "turn": turn + 1,
            "mode": resp["mode"],
            "text": resp.get("answer", ""),
            "answer": resp.get("answer", ""),
            "sql": resp.get("sql", ""),
            "results": resp.get("results", []),
            "confidence": resp.get("confidence", 0),
            "chart_hint": resp.get("chart_hint", "bar"),
            "error": resp.get("error"),
        }
        _render(entry, result_limit=4)
        st.caption(f"Resolved in {_ms} ms")

    st.session_state["a5_history"].append(entry)

with st.sidebar:
    st.button("Sync Snowflake", on_click=clear_all_caches,
              use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
