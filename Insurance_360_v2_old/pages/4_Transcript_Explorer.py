"""
Page 4 -- TRANSCRIPT EXPLORER (RAG)   (Bauhaus / Neo-Brutalist)
Built from stitch_snowflake_streamlit_ui_redesign/transcript_explorer_rag/

Retrieval runs through SNOWFLAKE.CORTEX.SEARCH_PREVIEW (see utils/rag_agent.py)
because snowflake.core is not installed in this runtime. The whole chain -
vector search plus a CORTEX.COMPLETE synthesis - is memoized on
(query, limit, customer_filter), so toggling the quality scores or opening a
transcript does not replay several seconds of AI work.
"""
import os
import sys
import time

import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import clear_all_caches  # noqa: E402
from utils.rag_agent import (  # noqa: E402
    answer_from_context, evaluate_rag_response, search_transcripts,
)
from utils.theme import (  # noqa: E402
    BLUE, INK, RED, apply_theme, banner, bento, kpi, loading,
    section, sidebar, topbar,
)

st.set_page_config(page_title="Transcript RAG // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

banner(
    "Transcript Explorer",
    "Semantic retrieval over <b>866</b> insurance call transcripts via Cortex "
    "Search, with a grounded synthesis from Cortex Complete. Ask in plain "
    "English &mdash; the engine ranks by meaning, not keywords.",
    eyebrow="Vector Retrieval // snowflake-arctic-embed-m-v1.5",
)

EXAMPLES = [
    "customers who mentioned cancelling their policy",
    "calls about delayed or rejected claims",
    "customers asking about renewal or premium increase",
    "complaints about poor service or long wait times",
    "customers interested in adding new coverage",
]

st.session_state.setdefault("t4_query", "")
st.session_state.setdefault("t4_k", 5)
st.session_state.setdefault("t4_cust", "")


def _commit() -> None:
    st.session_state["t4_query"] = st.session_state["_t4_q"].strip()
    st.session_state["t4_k"] = st.session_state["_t4_k"]
    st.session_state["t4_cust"] = st.session_state["_t4_c"].strip()


section("Retrieval Query", "01")

with st.form("t4_search", border=True):
    q1, q2 = st.columns([4, 1])
    with q1:
        st.text_input("Natural Language Query",
                      value=st.session_state["t4_query"],
                      placeholder="e.g. customers upset about claim delays",
                      key="_t4_q")
    with q2:
        _ks = [3, 5, 8, 10]
        st.selectbox("Top K", _ks, index=_ks.index(st.session_state["t4_k"]),
                     key="_t4_k")
    st.text_input("Scope To Customer ID (optional)",
                  value=st.session_state["t4_cust"],
                  placeholder="e.g. CUST00758", key="_t4_c")
    st.form_submit_button("Execute Retrieval", type="primary",
                          on_click=_commit, use_container_width=True)

ex_cols = st.columns(len(EXAMPLES))
for i, ex in enumerate(EXAMPLES):
    if ex_cols[i].button(ex, key=f"t4_ex_{i}", use_container_width=True):
        st.session_state["t4_query"] = ex
        st.rerun()

eval_mode = st.toggle("Score RAG quality (groundedness / context / answer)",
                      key="t4_eval",
                      help="Runs an additional Cortex Complete scoring call.")

query = st.session_state["t4_query"]
if not query:
    st.html('<div class="bh-box paper"><div class="bh-box-title">'
            '<span>Awaiting Query</span><span>Idle</span></div>'
            '<div style="font-family:var(--font-body);font-size:0.88rem;'
            'color:var(--muted)">Enter a query above, or pick one of the '
            'example probes, to search the transcript corpus.</div></div>')
    st.stop()

_t0 = time.perf_counter()
with loading("Cortex Search retrieving"):
    try:
        resp = search_transcripts(
            query,
            limit=st.session_state["t4_k"],
            customer_filter=st.session_state["t4_cust"] or None,
        )
    except Exception as e:
        st.error(f"Cortex Search error: {e}")
        st.info("Verify the service: SHOW CORTEX SEARCH SERVICES IN SCHEMA SILVER;")
        st.stop()
_ms = int((time.perf_counter() - _t0) * 1000)

results = resp.get("results", [])
rag_answer = resp.get("rag_answer", "")

topbar(records=f"{len(results)} hits", latency=f"{_ms} ms", schema="SILVER")

if results:
    sents = [float(r.get("SENTIMENT_SCORE") or 0) for r in results]
    neg = sum(1 for s in sents if s < -0.3)
    intents = {}
    for r in results:
        k = str(r.get("CUSTOMER_INTENT") or "unknown")
        intents[k] = intents.get(k, 0) + 1
    top_intent = max(intents, key=intents.get)
    bento([
        kpi("Hits", f"{len(results)}", "Ranked by vector similarity", icon="◼"),
        kpi("Avg Sentiment", f"{(sum(sents) / len(sents)):+.3f}",
            "Across retrieved calls",
            tone="red" if sum(sents) / len(sents) < 0 else "yellow", icon="◉"),
        kpi("Negative Calls", f"{neg}", "Sentiment below -0.30",
            tone="paper", icon="▲"),
        kpi("Dominant Intent", top_intent.replace("_", " ").title(),
            f"{intents[top_intent]} of {len(results)}", tone="dark", icon="◈"),
    ])

# ── RAG answer ────────────────────────────────────────────────
if rag_answer:
    section("Grounded Synthesis", "02")
    st.html(
        '<div class="bh-box yellow"><div class="bh-box-title" '
        'style="border-bottom-color:var(--ink)">'
        '<span>Cortex Search + Complete</span><span>RAG</span></div>'
        f'<div style="font-family:var(--font-body);font-size:0.92rem;'
        f'line-height:1.7;color:var(--ink)">{rag_answer}</div></div>')

    if eval_mode and results:
        with loading("Scoring RAG quality"):
            scores = evaluate_rag_response(
                query, rag_answer,
                tuple(str(r.get("CALL_SUMMARY") or "") for r in results[:3]))
        tiles = []
        for label, key in [("Groundedness", "groundedness"),
                           ("Context Relevance", "context_relevance"),
                           ("Answer Relevance", "answer_relevance")]:
            v = scores[key]
            tiles.append(kpi(label, f"{v:.2f}", "of 1.00",
                             tone="yellow" if v >= 0.75 else "red",
                             icon="✓" if v >= 0.75 else "!",
                             bar_pct=int(v * 100),
                             bar_color=INK if v >= 0.75 else RED))
        bento(tiles)

# ── Result ledger ─────────────────────────────────────────────
if not results:
    st.warning("No transcripts matched. Try different phrasing.")
    st.stop()

section(f"Matched Transcripts ({len(results)})", "03")


def _card(i: int, r) -> str:
    s = float(r.get("SENTIMENT_SCORE") or 0)
    tone = "red" if s < -0.3 else "yellow" if s < 0.1 else "ghost"
    intent = str(r.get("CUSTOMER_INTENT") or "unknown").replace("_", " ").title()
    return f"""
    <div class="bh-box tight" style="margin-bottom:14px">
        <div class="bh-box-title">
            <span>{i:02d} // {r.get('CUSTOMER_NAME') or 'Unknown'}</span>
            <span style="color:{RED if s < -0.3 else INK}">{round(s, 2)} sentiment</span>
        </div>
        <div style="margin-bottom:10px">
            <span class="bh-chip {tone}">{intent}</span>
            <span class="bh-chip ghost">{r.get('CUSTOMER_ID') or ''}</span>
            <span class="bh-chip bluesoft">{r.get('SEGMENT') or ''}</span>
            <span class="bh-chip ghost">{str(r.get('INTERACTION_DATE') or '')[:10]}</span>
            <span class="bh-chip ghost">{r.get('CHANNEL') or ''}</span>
        </div>
        <div class="bh-kv"><span class="bh-kv-k">Subject</span>
            <span class="bh-kv-v">{r.get('SUBJECT') or ''}</span></div>
        <div style="font-family:var(--font-body);font-size:0.86rem;
                    line-height:1.65;color:var(--muted);margin-top:10px">
            {r.get('CALL_SUMMARY') or ''}</div>
        <div style="font-family:var(--font-mono);font-size:0.62rem;font-weight:700;
                    text-transform:uppercase;color:{BLUE};margin-top:10px;
                    border-top:1px dashed var(--hairline);padding-top:8px">
            Topics: {r.get('KEY_TOPICS') or '—'}</div>
    </div>"""


st.html("".join(_card(i + 1, r) for i, r in enumerate(results)))

# ── Transcript viewer ─────────────────────────────────────────
section("Full Transcript", "04")
tx_map = {
    f"{i + 1:02d} // {r.get('CUSTOMER_NAME') or 'Unknown'} // "
    f"{str(r.get('INTERACTION_DATE') or '')[:10]}": i
    for i, r in enumerate(results)
}
pick = st.selectbox("Select Call", list(tx_map.keys()), key="t4_pick")
sel = results[tx_map[pick]]

v1, v2 = st.columns([3, 1])
with v1:
    st.html(f'<div class="bh-mono">{sel.get("TRANSCRIPT_TEXT") or ""}</div>')
with v2:
    _s = float(sel.get("SENTIMENT_SCORE") or 0)
    st.html(f"""
    <div class="bh-box tight">
        <div class="bh-box-title"><span>Call Meta</span></div>
        <div class="bh-kv"><span class="bh-kv-k">Call ID</span>
            <span class="bh-kv-v">{sel.get('CALL_ID') or ''}</span></div>
        <div class="bh-kv"><span class="bh-kv-k">Customer</span>
            <span class="bh-kv-v">{sel.get('CUSTOMER_ID') or ''}</span></div>
        <div class="bh-kv"><span class="bh-kv-k">Channel</span>
            <span class="bh-kv-v">{sel.get('CHANNEL') or ''}</span></div>
        <div class="bh-kv"><span class="bh-kv-k">Intent</span>
            <span class="bh-kv-v">{str(sel.get('CUSTOMER_INTENT') or '').replace('_', ' ').title()}</span></div>
        <div class="bh-kv"><span class="bh-kv-k">Sentiment</span>
            <span class="bh-kv-v" style="color:{RED if _s < -0.3 else INK}">{round(_s, 4)}</span></div>
        <div style="margin-top:12px">
            <div class="bh-meter {'red' if _s < 0 else ''}">
                <i style="width:{max(2, min(100, int((_s + 1) / 2 * 100)))}%"></i></div>
            <div class="bh-meter-scale"><span>-1</span><span>0</span><span>+1</span></div>
        </div>
    </div>""")
    st.caption(f"Open Customer 360 and search {sel.get('CUSTOMER_ID')} "
               "for the full profile.")

# ── Follow-up ─────────────────────────────────────────────────
section("Grounded Follow-Up", "05")
st.caption("Answered using only the transcripts retrieved above")

with st.form("t4_follow", border=True):
    followup = st.text_input(
        "Follow-Up Question",
        placeholder="e.g. what resolution did these customers receive?")
    asked = st.form_submit_button("Ask", type="primary",
                                 use_container_width=True)

if asked and followup.strip():
    summaries = tuple(
        f"Customer: {r.get('CUSTOMER_NAME')}\n"
        f"Subject: {r.get('SUBJECT') or ''}\n"
        f"Summary: {r.get('CALL_SUMMARY') or ''}"
        for r in results)
    with loading("Cortex Complete reasoning"):
        ans = answer_from_context(followup.strip(), summaries)
    st.html('<div class="bh-box blue"><div class="bh-box-title">'
            '<span>Grounded Answer</span><span>Context-Only</span></div>'
            f'<div style="font-family:var(--font-body);font-size:0.9rem;'
            f'line-height:1.7;color:var(--ink)">{ans}</div></div>')

with st.sidebar:
    st.button("Sync Snowflake", on_click=clear_all_caches,
              use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
