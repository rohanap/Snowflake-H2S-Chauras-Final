"""
Page 6 -- DOCUMENT & AUDIO INTELLIGENCE   (Bauhaus / Neo-Brutalist)
Built from stitch_snowflake_streamlit_ui_redesign/document_audio_ai/
  sections: KPI bento (4 tiles) / segmented view switcher / filter+search bar /
            document ledger + pagination / split deep-dive inspection card /
            raw extracted key-values WITH PARSING CHECKS / 2 charts

The mockup's "Raw Extracted Key-Values Box with Parsing Checks" maps directly
onto a real data-quality problem in this table: AI_EXTRACT returned free text
for some money fields ('None', '30 lakhs', '2%'), and casting those with
::FLOAT crashes the page. Every numeric JSON read uses TRY_TO_DOUBLE, and the
unparseable values are surfaced rather than hidden.
"""
import json
import math
import os
import sys
import time

import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import clear_all_caches, run_query  # noqa: E402
from utils.theme import (  # noqa: E402
    INK, RED, YELLOW, apply_theme, banner, bento, inr, kpi,
    loading, section, sidebar, topbar,
)

st.set_page_config(page_title="Document AI // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

DOCS = "INSURANCE_C360.SILVER.EXTRACTED_POLICY_DOCS"
AUDIO = "INSURANCE_C360.SILVER.AUDIO_TRANSCRIPTIONS"
_q = run_query
PAGE_SIZE = 12

# TRY_TO_DOUBLE, never ::FLOAT - see module docstring.
_NUM = "TRY_TO_DOUBLE(EXTRACTED_FIELDS:response:{f}::VARCHAR)"


def _num(field: str) -> str:
    return _NUM.format(f=field)


# ── Cached loaders ────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def load_doc_stats() -> pd.DataFrame:
    return _q(f"""
        SELECT COUNT(*) AS TOTAL_DOCS,
            COUNT(DISTINCT EXTRACTED_FIELDS:response:policy_type::VARCHAR) AS POLICY_TYPES,
            ROUND(AVG({_num('premium')}), 2) AS AVG_PREMIUM,
            ROUND(AVG({_num('deductible')}), 2) AS AVG_DEDUCTIBLE,
            ROUND(SUM({_num('sum_insured')}), 2) AS TOTAL_INSURED,
            COUNT_IF({_num('premium')} IS NULL
                     AND EXTRACTED_FIELDS:response:premium IS NOT NULL)
              + COUNT_IF({_num('deductible')} IS NULL
                     AND EXTRACTED_FIELDS:response:deductible IS NOT NULL)
              + COUNT_IF({_num('sum_insured')} IS NULL
                     AND EXTRACTED_FIELDS:response:sum_insured IS NOT NULL)
              AS UNPARSEABLE
        FROM {DOCS}
    """)


@st.cache_data(ttl=1800, show_spinner=False)
def load_audio_stats() -> pd.DataFrame:
    return _q(f"""
        SELECT COUNT(*) AS AUDIO_FILES,
               ROUND(AVG(SENTIMENT_SCORE), 4) AS AVG_SENT,
               COUNT(DISTINCT CUSTOMER_INTENT) AS INTENTS
        FROM {AUDIO}
    """)


@st.cache_data(ttl=1800, show_spinner=False)
def load_policy_types() -> list:
    df = _q(f"""
        SELECT DISTINCT EXTRACTED_FIELDS:response:policy_type::VARCHAR AS T
        FROM {DOCS}
        WHERE EXTRACTED_FIELDS:response:policy_type IS NOT NULL ORDER BY 1
    """)
    return df["T"].dropna().tolist()


@st.cache_data(ttl=1800, max_entries=50, show_spinner=False)
def load_docs(policy_type: str | None, term: str | None) -> pd.DataFrame:
    where, params = ["1=1"], []
    if policy_type:
        where.append("EXTRACTED_FIELDS:response:policy_type::VARCHAR = ?")
        params.append(policy_type)
    if term:
        where.append("PARSED_TEXT ILIKE ?")
        params.append(f"%{term}%")
    return _q(f"""
        SELECT EXTRACTED_FIELDS:response:policy_number::VARCHAR AS POLICY_NUMBER,
            EXTRACTED_FIELDS:response:policy_type::VARCHAR AS POLICY_TYPE,
            EXTRACTED_FIELDS:response:customer_name::VARCHAR AS CUSTOMER_NAME,
            EXTRACTED_FIELDS:response:customer_id::VARCHAR AS CUSTOMER_ID,
            {_num('premium')} AS PREMIUM,
            {_num('sum_insured')} AS SUM_INSURED,
            {_num('deductible')} AS DEDUCTIBLE,
            EXTRACTED_FIELDS:response:start_date::VARCHAR AS START_DATE,
            EXTRACTED_FIELDS:response:end_date::VARCHAR AS END_DATE,
            FILE_NAME
        FROM {DOCS}
        WHERE {' AND '.join(where)}
        ORDER BY 1
    """, params)


@st.cache_data(ttl=1800, max_entries=100, show_spinner=False)
def load_doc_detail(policy_number: str) -> pd.DataFrame:
    return _q(f"""
        SELECT EXTRACTED_FIELDS:response:benefits::VARCHAR AS BENEFITS,
            EXTRACTED_FIELDS:response:exclusions::VARCHAR AS EXCLUSIONS,
            EXTRACTED_FIELDS:response:premium::VARCHAR AS RAW_PREMIUM,
            EXTRACTED_FIELDS:response:deductible::VARCHAR AS RAW_DEDUCTIBLE,
            EXTRACTED_FIELDS:response:sum_insured::VARCHAR AS RAW_SUM_INSURED,
            EXTRACTED_FIELDS:response:policy_type::VARCHAR AS POLICY_TYPE,
            EXTRACTED_FIELDS:response:customer_name::VARCHAR AS CUSTOMER_NAME,
            FILE_NAME,
            LEFT(PARSED_TEXT, 2500) AS FULL_TEXT
        FROM {DOCS}
        WHERE EXTRACTED_FIELDS:response:policy_number::VARCHAR = ?
    """, [policy_number])


@st.cache_data(ttl=1800, show_spinner=False)
def load_by_type() -> pd.DataFrame:
    return _q(f"""
        SELECT EXTRACTED_FIELDS:response:policy_type::VARCHAR AS POLICY_TYPE,
            COUNT(*) AS DOC_COUNT,
            ROUND(AVG({_num('premium')}), 2) AS AVG_PREMIUM,
            ROUND(AVG({_num('deductible')}), 2) AS AVG_DEDUCTIBLE
        FROM {DOCS} GROUP BY 1 ORDER BY 2 DESC
    """)


@st.cache_data(ttl=1800, show_spinner=False)
def load_audio_list() -> pd.DataFrame:
    return _q(f"""
        SELECT FILE_NAME, CALL_ID, CUSTOMER_ID,
            SENTIMENT_SCORE, CUSTOMER_INTENT,
            LEFT(CALL_SUMMARY, 220) AS SUMMARY
        FROM {AUDIO} ORDER BY FILE_NAME
    """)


@st.cache_data(ttl=1800, max_entries=100, show_spinner=False)
def load_call_detail(call_id: str) -> pd.DataFrame:
    return _q(f"""
        SELECT TRANSCRIBED_TEXT, SENTIMENT_SCORE, CALL_SUMMARY,
               CUSTOMER_INTENT, FILE_NAME, CUSTOMER_ID
        FROM {AUDIO} WHERE CALL_ID = ?
    """, [call_id])


def _clear_all() -> None:
    for fn in (load_doc_stats, load_audio_stats, load_policy_types, load_docs,
               load_doc_detail, load_by_type, load_audio_list, load_call_detail):
        fn.clear()
    clear_all_caches()


# ── Banner + KPI bento ────────────────────────────────────────
banner(
    "Document & Audio Intelligence",
    "Structured extraction from policy PDFs via <b>AI_PARSE_DOCUMENT</b> and "
    "<b>AI_EXTRACT</b>, plus call-recording transcription via "
    "<b>AI_TRANSCRIBE</b> chained into sentiment, summarisation and intent "
    "classification.",
    eyebrow="Unstructured Pipeline // Cortex AI",
)

_t0 = time.perf_counter()
with loading("Reading extraction index"):
    stats = load_doc_stats()
    astats = load_audio_stats()
_ms = int((time.perf_counter() - _t0) * 1000)

r = stats.iloc[0]
a = astats.iloc[0]
bad = int(r["UNPARSEABLE"] or 0)
total_docs = int(r["TOTAL_DOCS"] or 0)

topbar(records=f"{total_docs} PDFs // {int(a['AUDIO_FILES'] or 0)} audio",
       latency=f"{_ms} ms", schema="SILVER")

bento([
    kpi("PDFs Processed", f"{total_docs}", "AI_PARSE + AI_EXTRACT",
        icon="◼", bar_pct=100, bar_color=INK),
    kpi("Policy Types", f"{int(r['POLICY_TYPES'] or 0)}",
        "Distinct products extracted", tone="yellow", icon="◈"),
    kpi("Avg Premium", inr(r["AVG_PREMIUM"], compact=True),
        "Numeric extractions only", tone="paper", icon="₹"),
    kpi("Audio Transcribed", f"{int(a['AUDIO_FILES'] or 0)}",
        f"Avg sentiment {float(a['AVG_SENT'] or 0):+.2f}", tone="dark",
        icon="◉"),
    kpi("Parse Failures", f"{bad}",
        "Non-numeric money fields",
        tone="red" if bad else "paper", icon="▲",
        bar_pct=int(bad / max(1, total_docs * 3) * 100), bar_color=RED),
])

if bad:
    st.html(
        '<div class="bh-box red tight"><div class="bh-box-title" '
        'style="border-bottom-color:var(--ink)">'
        '<span>Extraction Quality Advisory</span><span>TRY_TO_DOUBLE</span></div>'
        f'<div style="font-family:var(--font-body);font-size:0.86rem;'
        f'line-height:1.6;color:var(--ink)">'
        f'<b>{bad}</b> extracted money value(s) are not numeric &mdash; AI_EXTRACT '
        'returned free text such as <code>30 lakhs</code> or <code>2%</code>. '
        'Those are treated as NULL in the aggregates above; the raw strings are '
        'shown per document in the deep-dive card below.</div></div>')

VIEWS = ["Policy Documents", "Audio Transcriptions"]
view = st.segmented_control("View", VIEWS, default=VIEWS[0], key="d6_view",
                            label_visibility="collapsed") or VIEWS[0]

# ══════════════════════════════════════════════════════════════
if view == VIEWS[0]:
    section("Document Ledger", "01")

    st.session_state.setdefault("d6_type", "All")
    st.session_state.setdefault("d6_term", "")
    st.session_state.setdefault("d6_page", 0)

    def _commit() -> None:
        st.session_state["d6_type"] = st.session_state["_d6_t"]
        st.session_state["d6_term"] = st.session_state["_d6_s"].strip()
        st.session_state["d6_page"] = 0

    types = load_policy_types()
    with st.form("d6_filters", border=True):
        f1, f2, f3 = st.columns([1, 2, 1])
        with f1:
            opts = ["All"] + types
            st.selectbox("Policy Type", opts,
                         index=opts.index(st.session_state["d6_type"])
                         if st.session_state["d6_type"] in opts else 0,
                         key="_d6_t")
        with f2:
            st.text_input("Full-Text Search", value=st.session_state["d6_term"],
                          placeholder="e.g. flood damage, hospitalization",
                          key="_d6_s")
        with f3:
            st.write("")
            st.form_submit_button("Filter", type="primary", on_click=_commit,
                                  use_container_width=True)

    with loading("Filtering ledger"):
        docs = load_docs(
            None if st.session_state["d6_type"] == "All" else st.session_state["d6_type"],
            st.session_state["d6_term"] or None)

    if docs.empty:
        st.info("No documents match the current filters.")
    else:
        pages = max(1, math.ceil(len(docs) / PAGE_SIZE))
        page = min(st.session_state["d6_page"], pages - 1)
        st.session_state["d6_page"] = page
        start = page * PAGE_SIZE
        chunk = docs.iloc[start:start + PAGE_SIZE]

        head = ("<tr><th>Policy</th><th>Type</th><th>Customer</th>"
                "<th>Premium</th><th>Sum Insured</th><th>Deductible</th>"
                "<th>Term</th></tr>")
        body = "".join(
            f"<tr><td><b>{d.POLICY_NUMBER or '—'}</b></td>"
            f"<td>{d.POLICY_TYPE or '—'}</td>"
            f"<td>{d.CUSTOMER_NAME or '—'}</td>"
            f"<td class='num'>{'—' if pd.isna(d.PREMIUM) else inr(d.PREMIUM)}</td>"
            f"<td class='num'>{'—' if pd.isna(d.SUM_INSURED) else inr(d.SUM_INSURED)}</td>"
            f"<td class='num'>{'—' if pd.isna(d.DEDUCTIBLE) else inr(d.DEDUCTIBLE)}</td>"
            f"<td>{str(d.START_DATE or '')[:10]} / {str(d.END_DATE or '')[:10]}</td></tr>"
            for d in chunk.itertuples())
        st.html(f'<table class="bh-ledger">{head}{body}</table>')

        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("◀ Prev", key="d6_prev", disabled=page == 0,
                         use_container_width=True):
                st.session_state["d6_page"] = page - 1
                st.rerun()
        with p2:
            st.html('<div style="text-align:center;font-family:var(--font-mono);'
                    'font-size:0.66rem;font-weight:700;letter-spacing:0.12em;'
                    'text-transform:uppercase;padding-top:11px;color:var(--muted)">'
                    f'Page {page + 1} / {pages} &nbsp;//&nbsp; '
                    f'{start + 1}&ndash;{min(start + PAGE_SIZE, len(docs))} '
                    f'of {len(docs)}</div>')
        with p3:
            if st.button("Next ▶", key="d6_next", disabled=page >= pages - 1,
                         use_container_width=True):
                st.session_state["d6_page"] = page + 1
                st.rerun()

        # ── Deep-dive inspection ──────────────────────────────
        section("Deep-Dive Inspection", "02")
        nums = [p for p in docs["POLICY_NUMBER"].tolist() if p]
        if nums:
            pick = st.selectbox("Policy Number", nums, key="d6_pick")
            with loading("Loading document"):
                det = load_doc_detail(pick)

            if not det.empty:
                d = det.iloc[0]

                def _pills(raw, cls) -> str:
                    try:
                        items = json.loads(raw)
                        if isinstance(items, list) and items:
                            return "".join(
                                f'<span class="bh-chip {cls}">{i}</span>'
                                for i in items)
                    except (TypeError, ValueError):
                        pass
                    return (f'<div style="font-family:var(--font-body);'
                            f'font-size:0.84rem;color:var(--muted)">'
                            f'{raw or "—"}</div>')

                st.html(
                    '<div class="bh-box dark tight"><div class="bh-box-title">'
                    f'<span>{pick} // {d["POLICY_TYPE"] or "—"}</span>'
                    f'<span>{d["CUSTOMER_NAME"] or "—"}</span></div>'
                    f'<div style="font-family:var(--font-mono);font-size:0.66rem;'
                    f'color:var(--dim)">SOURCE: {d["FILE_NAME"]}</div></div>')

                dc1, dc2 = st.columns(2)
                with dc1:
                    st.html('<div class="bh-box"><div class="bh-box-title">'
                            '<span>Coverage &amp; Benefits</span>'
                            '<span>AI_EXTRACT</span></div>'
                            f'{_pills(d["BENEFITS"], "bluesoft")}</div>')
                with dc2:
                    st.html('<div class="bh-box red"><div class="bh-box-title" '
                            'style="border-bottom-color:var(--ink)">'
                            '<span>Exclusions</span><span>AI_EXTRACT</span></div>'
                            f'{_pills(d["EXCLUSIONS"], "red")}</div>')

                # Raw values + parsing checks (straight from the mockup)
                raw_rows = []
                for label, col in (("Premium", "RAW_PREMIUM"),
                                   ("Sum Insured", "RAW_SUM_INSURED"),
                                   ("Deductible", "RAW_DEDUCTIBLE")):
                    val = d[col]
                    txt = "—" if val is None else str(val)
                    try:
                        float(txt)
                        ok = True
                    except ValueError:
                        ok = False
                    flag = ('<span class="bh-chip ghost" style="margin-left:8px">'
                            'PARSED</span>' if ok else
                            '<span class="bh-chip red" style="margin-left:8px">'
                            'NOT NUMERIC</span>')
                    raw_rows.append(
                        f'<div class="bh-kv"><span class="bh-kv-k">{label}</span>'
                        f'<span class="bh-kv-v">{txt}{flag}</span></div>')
                st.html('<div class="bh-box paper"><div class="bh-box-title">'
                        '<span>Raw Extracted Key-Values</span>'
                        '<span>Parsing Checks</span></div>'
                        f'{"".join(raw_rows)}</div>')

                if st.toggle("Open Parsed Document", key="d6_full"):
                    st.html(f'<div class="bh-mono">{d["FULL_TEXT"]}</div>')

    # ── Distribution ──────────────────────────────────────────
    section("Portfolio Distribution", "03")
    with loading("Aggregating by product"):
        bt = load_by_type()
    if not bt.empty:
        mx_c = float(bt["DOC_COUNT"].max()) or 1.0
        mx_p = float(bt["AVG_PREMIUM"].max() or 1) or 1.0
        g1, g2 = st.columns(2)
        with g1:
            bars = "".join(
                f'<div><div class="bh-bar-l"><span>{x.POLICY_TYPE}</span>'
                f'<span>{int(x.DOC_COUNT)}</span></div>'
                f'<div class="bh-bar-t"><i style="width:'
                f'{max(2, int(x.DOC_COUNT / mx_c * 100))}%;background:{INK}"></i>'
                f'</div></div>' for x in bt.itertuples())
            st.html('<div class="bh-box"><div class="bh-box-title">'
                    '<span>Documents By Type</span><span>Count</span></div>'
                    f'<div class="bh-bars">{bars}</div></div>')
        with g2:
            bars = "".join(
                f'<div><div class="bh-bar-l"><span>{x.POLICY_TYPE}</span>'
                f'<span>{inr(x.AVG_PREMIUM)} / {inr(x.AVG_DEDUCTIBLE)}</span></div>'
                f'<div class="bh-bar-t"><i style="width:'
                f'{max(2, int((x.AVG_PREMIUM or 0) / mx_p * 100))}%;'
                f'background:{YELLOW}"></i></div></div>'
                for x in bt.itertuples())
            st.html('<div class="bh-box"><div class="bh-box-title">'
                    '<span>Avg Premium / Deductible</span><span>₹</span></div>'
                    f'<div class="bh-bars">{bars}</div></div>')

# ══════════════════════════════════════════════════════════════
else:
    section("Audio Pipeline", "01")
    st.html(
        '<div class="bh-box dark tight"><div class="bh-box-title">'
        '<span>Chain</span><span>5 Stages</span></div>'
        '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:0">'
        '<span class="bh-chip" style="background:var(--yellow);color:var(--ink);'
        'border-color:var(--paper)">MP3 AUDIO</span>'
        '<span style="color:var(--paper);margin:0 8px 5px 3px">&rarr;</span>'
        '<span class="bh-chip" style="background:var(--paper);color:var(--ink)">AI_TRANSCRIBE</span>'
        '<span style="color:var(--paper);margin:0 8px 5px 3px">&rarr;</span>'
        '<span class="bh-chip" style="background:var(--paper);color:var(--ink)">CORTEX.SENTIMENT</span>'
        '<span style="color:var(--paper);margin:0 8px 5px 3px">&rarr;</span>'
        '<span class="bh-chip" style="background:var(--paper);color:var(--ink)">CORTEX.SUMMARIZE</span>'
        '<span style="color:var(--paper);margin:0 8px 5px 3px">&rarr;</span>'
        '<span class="bh-chip" style="background:var(--paper);color:var(--ink)">AI_CLASSIFY</span>'
        '</div></div>')

    with loading("Reading transcriptions"):
        audio = load_audio_list()

    if audio.empty:
        st.info("No audio transcriptions available.")
    else:
        section("Transcription Ledger", "02")
        head = ("<tr><th>Call</th><th>Customer</th><th>Intent</th>"
                "<th>Sentiment</th><th>File</th></tr>")
        body = "".join(
            f"<tr><td><b>{x.CALL_ID}</b></td><td>{x.CUSTOMER_ID}</td>"
            f"<td>{str(x.CUSTOMER_INTENT or '').replace('_', ' ').title()}</td>"
            f"<td class='num' style='color:"
            f"{RED if float(x.SENTIMENT_SCORE or 0) < -0.3 else INK}'>"
            f"{float(x.SENTIMENT_SCORE or 0):+.4f}</td>"
            f"<td>{x.FILE_NAME}</td></tr>" for x in audio.itertuples())
        st.html(f'<table class="bh-ledger">{head}{body}</table>')

        section("Call Analysis", "03")
        pick = st.selectbox("Call ID", audio["CALL_ID"].tolist(), key="d6_call")
        with loading("Loading call"):
            cd = load_call_detail(pick)

        if not cd.empty:
            c = cd.iloc[0]
            s = float(c["SENTIMENT_SCORE"] or 0)
            pct = min(100, max(2, int((s + 1) / 2 * 100)))
            a1, a2 = st.columns([1, 1])
            with a1:
                st.html(f"""
                <div class="bh-box">
                    <div class="bh-box-title"><span>Signal</span>
                        <span>{c['FILE_NAME']}</span></div>
                    <div class="bh-kv"><span class="bh-kv-k">Customer</span>
                        <span class="bh-kv-v">{c['CUSTOMER_ID']}</span></div>
                    <div class="bh-kv"><span class="bh-kv-k">Intent</span>
                        <span class="bh-kv-v">
                        <span class="bh-chip bluesoft">{str(c['CUSTOMER_INTENT'] or '').replace('_', ' ').title()}</span>
                        </span></div>
                    <div class="bh-kv"><span class="bh-kv-k">Sentiment</span>
                        <span class="bh-kv-v" style="color:{RED if s < -0.3 else INK}">{s:+.4f}</span></div>
                    <div style="margin-top:14px">
                        <div class="bh-meter {'red' if s < 0 else ''}">
                            <i style="width:{pct}%"></i></div>
                        <div class="bh-meter-scale"><span>-1</span><span>0</span>
                            <span>+1</span></div>
                    </div>
                </div>""")
            with a2:
                st.html('<div class="bh-box yellow"><div class="bh-box-title" '
                        'style="border-bottom-color:var(--ink)">'
                        '<span>AI Summary</span><span>CORTEX.SUMMARIZE</span></div>'
                        f'<div style="font-family:var(--font-body);'
                        f'font-size:0.88rem;line-height:1.65;color:var(--ink)">'
                        f'{c["CALL_SUMMARY"]}</div></div>')

            if st.toggle("Open Full Transcription", key="d6_audio_full"):
                st.html(f'<div class="bh-mono">{c["TRANSCRIBED_TEXT"]}</div>')

st.caption("Powered by AI_PARSE_DOCUMENT // AI_EXTRACT // AI_TRANSCRIBE")

with st.sidebar:
    st.button("Sync Snowflake", on_click=_clear_all, use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
