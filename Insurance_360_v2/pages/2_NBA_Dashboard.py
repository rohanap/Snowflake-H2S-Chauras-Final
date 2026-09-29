"""
Page 2 -- NBA PRIORITY DASHBOARD   (Bauhaus / Neo-Brutalist)
Built from stitch_snowflake_streamlit_ui_redesign/nba_priority_dashboard/

Mockup -> Streamlit mapping:
  * 5-card KPI bento           -> theme.bento() + theme.kpi()
  * chip filter bar            -> st.form (one rerun on submit) + multiselects
                                  styled as brutalist chips
  * numbered execution queue   -> one st.html block per page of results, so a
                                  25-row page costs ~1 element instead of ~250
  * DRAFT OUTREACH per row     -> a single picker + panel inside a fragment
                                  (the mockup's JS drawer has no Streamlit
                                  equivalent; per-row buttons would mean
                                  hundreds of widgets)
  * right rail breakdowns      -> hand-drawn .bh-bar blocks, no chart library
  * "Batch Action (48)" alert  -> st.toast + a real queued count
"""
import math
import os
import sys
import time

import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import (  # noqa: E402
    clear_all_caches, generate_nba_message, load_all_360,
    load_customer_360, load_customer_confidence, load_nba_message,
)
from utils.theme import (  # noqa: E402
    INK, MUTED, PRI_INK, RED, YELLOW, apply_theme, banner, bento,
    inr, kpi, loading, section, sidebar, topbar,
)

st.set_page_config(page_title="NBA Priority // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

PRI_ORDER = ["Urgent", "High", "Medium", "Low"]
PAGE_SIZE = 25

banner(
    "NBA Priority Dashboard",
    "Scenario 10 rules triage: <b>Urgent</b> (churn &gt; 0.5 + failed payment), "
    "<b>High</b> (churn &gt; 0.4 + complaint), <b>Medium</b> (single policy + LTV &gt; ₹3,000).",
    eyebrow="Realtime Decision Stream // Engine-S10",
)

_t0 = time.perf_counter()
with loading("Loading decision stream (first load ~3s, then cached)"):
    df = load_all_360()
_ms = int((time.perf_counter() - _t0) * 1000)

if df.empty:
    st.warning("No customer data available.")
    st.stop()

topbar(records=f"{len(df):,}", latency=f"{_ms} ms")

# ── KPI bento ─────────────────────────────────────────────────
counts = df["NBA_PRIORITY"].value_counts()
total = len(df)
ltv_risk = df.loc[df["CHURN_RISK_LABEL"] == "High", "LIFETIME_VALUE"].sum()


def _pct(n):
    return int(round(n / total * 100)) if total else 0


bento([
    kpi("Urgent Triage", f"{int(counts.get('Urgent', 0)):,}",
        "Immediate intervention required", tone="red", icon="▲",
        bar_pct=_pct(counts.get("Urgent", 0)), bar_color=RED),
    kpi("High Priority", f"{int(counts.get('High', 0)):,}",
        "Escalated within 4 hours", icon="◤",
        bar_pct=_pct(counts.get("High", 0)), bar_color=INK),
    kpi("Medium Priority", f"{int(counts.get('Medium', 0)):,}",
        "24-hour SLA dispatch", tone="yellow", icon="◼",
        bar_pct=_pct(counts.get("Medium", 0)), bar_color=INK),
    kpi("Low / Standard", f"{int(counts.get('Low', 0)):,}",
        "Automated nudge cycle", tone="paper", icon="●",
        bar_pct=_pct(counts.get("Low", 0)), bar_color=MUTED),
    kpi("LTV At Risk", inr(ltv_risk, compact=True),
        f"Across {total:,} evaluated", tone="dark", icon="₹"),
])

# ── Filter bar ────────────────────────────────────────────────
_SEGMENTS = sorted(df["SEGMENT"].dropna().unique().tolist())
_CHANNELS = sorted(df["NBA_CHANNEL"].dropna().unique().tolist())

st.session_state.setdefault("v2_pri", ["Urgent", "High"])
st.session_state.setdefault("v2_seg", _SEGMENTS)
st.session_state.setdefault("v2_ch", _CHANNELS)
st.session_state.setdefault("v2_sort", "Churn Risk ↓")
st.session_state.setdefault("v2_page", 0)

SORT_MAP = {
    "Churn Risk ↓": "CHURN_RISK_SCORE",
    "LTV ↓": "LIFETIME_VALUE",
    "Failed Payments ↓": "FAILED_PAYMENT_COUNT",
    "Complaints ↓": "COMPLAINT_COUNT",
}


def _apply() -> None:
    st.session_state["v2_pri"] = st.session_state["_p"]
    st.session_state["v2_seg"] = st.session_state["_s"]
    st.session_state["v2_ch"] = st.session_state["_c"]
    st.session_state["v2_sort"] = st.session_state["_o"]
    st.session_state["v2_page"] = 0


st.html('<div class="bh-section"><span class="n">01</span>'
        '<span>Triage Pipeline Filters</span></div>')

with st.form("v2_filters", border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.multiselect("Priority Tier", PRI_ORDER,
                       default=st.session_state["v2_pri"], key="_p")
    with c2:
        st.multiselect("Segment", _SEGMENTS,
                       default=st.session_state["v2_seg"], key="_s")
    with c3:
        st.multiselect("Dispatch Channel", _CHANNELS,
                       default=st.session_state["v2_ch"], key="_c")
    with c4:
        st.selectbox("Rank By", list(SORT_MAP.keys()),
                     index=list(SORT_MAP).index(st.session_state["v2_sort"]),
                     key="_o")
    st.form_submit_button("Execute Query", type="primary",
                          on_click=_apply, use_container_width=True)


def _filtered():
    """Recompute from the cached frame; reads the loader so fragment-only
    reruns are self-contained (cache hit, costs nothing)."""
    out = load_all_360()
    if st.session_state["v2_pri"]:
        out = out[out["NBA_PRIORITY"].isin(st.session_state["v2_pri"])]
    if st.session_state["v2_seg"]:
        out = out[out["SEGMENT"].isin(st.session_state["v2_seg"])]
    if st.session_state["v2_ch"]:
        out = out[out["NBA_CHANNEL"].isin(st.session_state["v2_ch"])]
    return out.sort_values(SORT_MAP[st.session_state["v2_sort"]],
                           ascending=False).reset_index(drop=True)


# ── Execution queue ───────────────────────────────────────────
def _queue_row(n: int, row) -> str:
    pri = row["NBA_PRIORITY"]
    accent = PRI_INK.get(pri, INK)
    cs = round(float(row["CHURN_RISK_SCORE"]) * 100, 1)
    sent = round(float(row["AVG_SENTIMENT_SCORE"] or 0), 2)
    fc = int(row["FAILED_PAYMENT_COUNT"])
    cc = int(row["COMPLAINT_COUNT"])
    return f"""
    <div class="bh-row {pri.lower()}">
        <div class="bh-row-n">{n:02d}</div>
        <div class="bh-row-nw">
            <div class="bh-row-name">{row['NAME']}</div>
            <div style="margin-top:6px">
                <span class="bh-chip {'red' if pri == 'Urgent' else 'yellow' if pri == 'Medium' else 'dark' if pri == 'High' else 'ghost'}">{pri}</span>
                <span class="bh-chip ghost">{row['SEGMENT']}</span>
                <span class="bh-chip ghost">{row['CUSTOMER_ID']}</span>
            </div>
            <div class="bh-row-meta">{row['CITY']}, {row['STATE']} &nbsp;//&nbsp; {row['NBA_CHANNEL']}</div>
        </div>
        <div class="bh-cell">
            <div class="bh-cell-v" style="color:{accent}">{cs}%</div>
            <div class="bh-cell-k">Churn</div>
        </div>
        <div class="bh-cell">
            <div class="bh-cell-v">{inr(row['LIFETIME_VALUE'], compact=True)}</div>
            <div class="bh-cell-k">LTV</div>
        </div>
        <div class="bh-cell">
            <div class="bh-cell-v" style="color:{RED if fc else INK}">{fc}</div>
            <div class="bh-cell-k">Failed Pay</div>
        </div>
        <div class="bh-cell">
            <div class="bh-cell-v" style="color:{RED if sent < -0.3 else INK}">{sent}</div>
            <div class="bh-cell-k">Sentiment</div>
        </div>
        <div class="bh-nba-strip">
            <span class="bh-chip dark">NBA</span>
            <b>{row['NBA_ACTION']}</b>
            <span>// {row['NBA_REASON']}</span>
            <span class="bh-chip bluesoft">{cc} complaint(s)</span>
        </div>
    </div>"""


def _outreach(page_df) -> None:
    """Draft/regenerate outreach. The mockup's per-row drawer becomes one
    picker + panel: per-row buttons would mean hundreds of widgets."""
    if page_df.empty:
        return
    section("Outreach Dispatch", "03")
    labels = {f"{r['NAME']}  //  {r['NBA_PRIORITY']}  //  {r['NBA_ACTION']}": i
              for i, r in page_df.iterrows()}
    pick = st.selectbox("Target Customer", list(labels.keys()), key="v2_pick")
    row = page_df.loc[labels[pick]]

    st.html(f"""
    <div class="bh-box yellow">
        <div class="bh-box-title"><span>Next Best Action</span>
            <span>{row['NBA_CHANNEL']}</span></div>
        <div style="font-family:var(--font-display);font-weight:900;
                    font-size:clamp(1.3rem,2.8vw,2.1rem);line-height:1;
                    letter-spacing:-0.03em;text-transform:uppercase">
            {row['NBA_ACTION']}</div>
        <p class="bh-sub" style="border-left-color:var(--ink);margin-top:12px">
            {row['NBA_REASON']}</p>
        <div class="bh-facts" style="margin-top:16px;border-top-color:var(--ink)">
            <div class="bh-fact"><div class="bh-fact-k">Churn</div>
                <div class="bh-fact-v">{round(float(row['CHURN_RISK_SCORE']) * 100, 1)}%</div></div>
            <div class="bh-fact"><div class="bh-fact-k">Value At Risk</div>
                <div class="bh-fact-v">{inr(row['LIFETIME_VALUE'])}</div></div>
            <div class="bh-fact"><div class="bh-fact-k">Failed Pay</div>
                <div class="bh-fact-v">{int(row['FAILED_PAYMENT_COUNT'])}</div></div>
            <div class="bh-fact"><div class="bh-fact-k">Tenure</div>
                <div class="bh-fact-v">{int(row['TENURE_DAYS'])}d</div></div>
        </div>
    </div>""")

    _conf, _conf_ex = load_customer_confidence(row["CUSTOMER_ID"])
    if _conf is not None:
        _cp = round((_conf or 0) * 100)
        st.html(f'<div class="bh-box tight"><div class="bh-box-title">'
                f'<span>NBA Confidence</span><span>{_cp}%</span></div>'
                f'<div class="bh-meter {"red" if _cp < 50 else ""}">'
                f'<i style="width:{max(2, _cp)}%"></i></div>'
                f'<div style="font-family:var(--font-body);font-size:0.82rem;'
                f'line-height:1.5;color:var(--muted);margin-top:8px">'
                f'{_conf_ex}</div></div>')

    pre = load_nba_message(row["CUSTOMER_ID"])
    if len(pre) > 20:
        st.html('<div class="bh-box tight"><div class="bh-box-title">'
                '<span>Agent Script // Pre-Generated</span>'
                '<span>Cortex Complete</span></div>'
                f'<div class="bh-mono">{pre}</div></div>')

    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("Regenerate Script", key="v2_regen",
                     use_container_width=True):
            with loading("Cortex Complete drafting"):
                msg = generate_nba_message(row)
            st.html('<div class="bh-box tight"><div class="bh-box-title">'
                    '<span>Agent Script // Live</span><span>mistral-large3</span>'
                    f'</div><div class="bh-mono dark">{msg}</div></div>')
    with b2:
        if st.button("Dispatch Email", key="v2_dispatch", type="primary",
                     use_container_width=True):
            from pages._email_helpers import dispatch_emails
            _script = pre if len(pre) > 20 else f"{row['NBA_ACTION']}: {row['NBA_REASON']}"
            full_row = load_customer_360(row["CUSTOMER_ID"])
            if full_row is None:
                st.error("Could not load full customer profile for email.")
            else:
                try:
                    with loading("Sending emails via Snowflake"):
                        internal_to, customer_to = dispatch_emails(full_row, _script)
                    st.success(
                        f"2 emails dispatched:\n\n"
                        f"**Internal team** -> {internal_to}\n\n"
                        f"**Customer** -> {customer_to}"
                    )
                except Exception as e:
                    st.error(f"Email dispatch failed: {e}")


@st.fragment
def queue_panel() -> None:
    """Fragment so paging and outreach never rebuild the KPIs or the rail."""
    filt = _filtered()
    n = len(filt)

    h1, h2 = st.columns([2, 1])
    with h1:
        st.html('<div class="bh-section"><span class="n">02</span>'
                f'<span>Execution Queue &mdash; {n:,} Records</span></div>')
    with h2:
        view = st.segmented_control(
            "View", ["Queue", "Ledger"], default="Queue",
            key="v2_view", label_visibility="collapsed") or "Queue"

    if n == 0:
        st.info("No customers match the current filters.")
        return

    if view == "Ledger":
        tbl = filt.copy()
        tbl["CHURN_PCT"] = (tbl["CHURN_RISK_SCORE"] * 100).round(1)
        st.dataframe(
            tbl[["NAME", "NBA_PRIORITY", "SEGMENT", "STATE", "CHURN_PCT",
                 "LIFETIME_VALUE", "FAILED_PAYMENT_COUNT", "COMPLAINT_COUNT",
                 "AVG_SENTIMENT_SCORE", "NBA_CHANNEL", "NBA_ACTION"]],
            use_container_width=True, hide_index=True, height=560,
            column_config={
                "NAME": st.column_config.TextColumn("Customer", width="medium"),
                "NBA_PRIORITY": st.column_config.TextColumn("Tier", width="small"),
                "SEGMENT": st.column_config.TextColumn("Segment", width="small"),
                "STATE": st.column_config.TextColumn("ST", width="small"),
                "CHURN_PCT": st.column_config.ProgressColumn(
                    "Churn", min_value=0, max_value=100, format="%.1f%%"),
                "LIFETIME_VALUE": st.column_config.NumberColumn("LTV", format="₹%.0f"),
                "FAILED_PAYMENT_COUNT": st.column_config.NumberColumn(
                    "Fail", format="%d", width="small"),
                "COMPLAINT_COUNT": st.column_config.NumberColumn(
                    "Cmpl", format="%d", width="small"),
                "AVG_SENTIMENT_SCORE": st.column_config.NumberColumn(
                    "Sent", format="%.2f", width="small"),
                "NBA_CHANNEL": st.column_config.TextColumn("Channel", width="small"),
                "NBA_ACTION": st.column_config.TextColumn("Action", width="large"),
            })
        page_df = filt.head(200)
    else:
        pages = max(1, math.ceil(n / PAGE_SIZE))
        page = min(st.session_state["v2_page"], pages - 1)
        st.session_state["v2_page"] = page
        start = page * PAGE_SIZE
        page_df = filt.iloc[start:start + PAGE_SIZE]

        st.html("".join(_queue_row(start + i + 1, r)
                        for i, (_, r) in enumerate(page_df.iterrows())))

        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("◀ Prev", key="v2_prev", disabled=page == 0,
                         use_container_width=True):
                st.session_state["v2_page"] = page - 1
                st.rerun(scope="fragment")
        with p2:
            st.html(
                '<div style="text-align:center;font-family:var(--font-mono);'
                'font-size:0.66rem;font-weight:700;letter-spacing:0.12em;'
                'text-transform:uppercase;padding-top:11px;color:var(--muted)">'
                f'Page {page + 1} / {pages} &nbsp;//&nbsp; '
                f'{start + 1}&ndash;{min(start + PAGE_SIZE, n)} of {n:,}</div>')
        with p3:
            if st.button("Next ▶", key="v2_next", disabled=page >= pages - 1,
                         use_container_width=True):
                st.session_state["v2_page"] = page + 1
                st.rerun(scope="fragment")

    d1, d2 = st.columns([1, 1])
    with d1:
        st.download_button("Export Queue (CSV)",
                           data=filt.to_csv(index=False).encode("utf-8"),
                           file_name="nba_queue.csv", mime="text/csv",
                           key="v2_dl", use_container_width=True)
    with d2:
        urgent_n = int((filt["NBA_PRIORITY"] == "Urgent").sum())
        if st.button(f"Batch Action ({urgent_n})", key="v2_batch",
                     use_container_width=True, disabled=urgent_n == 0):
            st.toast(f"Triage engine: {urgent_n} Urgent customers queued for "
                     "automated high-touch dispatch.", icon="⚡")

    _outreach(page_df)


queue_panel()

# ── Right-rail style breakdowns (hand-drawn, no chart library) ─
section("Distribution Analysis", "04")
r1, r2, r3 = st.columns(3)

with r1:
    bars = []
    mx = int(counts.max()) if len(counts) else 1
    for p in PRI_ORDER:
        v = int(counts.get(p, 0))
        bars.append(
            f'<div><div class="bh-bar-l"><span>{p}</span><span>{v:,}</span></div>'
            f'<div class="bh-bar-t"><i style="width:{max(2, int(v / mx * 100))}%;'
            f'background:{PRI_INK.get(p, INK)}"></i></div></div>')
    st.html('<div class="bh-box"><div class="bh-box-title">'
            '<span>Customers By Tier</span><span>Count</span></div>'
            f'<div class="bh-bars">{"".join(bars)}</div></div>')

with r2:
    ltv = df.groupby("NBA_PRIORITY")["LIFETIME_VALUE"].sum().reindex(
        PRI_ORDER, fill_value=0)
    mx = float(ltv.max()) or 1.0
    bars = []
    for p in PRI_ORDER:
        v = float(ltv.get(p, 0))
        bars.append(
            f'<div><div class="bh-bar-l"><span>{p}</span>'
            f'<span>{inr(v, compact=True)}</span></div>'
            f'<div class="bh-bar-t"><i style="width:{max(2, int(v / mx * 100))}%;'
            f'background:{YELLOW}"></i></div></div>')
    st.html('<div class="bh-box"><div class="bh-box-title">'
            '<span>LTV At Stake</span><span>By Tier</span></div>'
            f'<div class="bh-bars">{"".join(bars)}</div></div>')

with r3:
    _u = (df["CHURN_RISK_SCORE"] > 0.5) & (df["FAILED_PAYMENT_COUNT"] > 0)
    _h = (df["CHURN_RISK_SCORE"] > 0.4) & (df["COMPLAINT_COUNT"] > 0) & ~_u
    _m = ((df["ACTIVE_POLICY_TYPE_COUNT"] == 1) &
          (df["LIFETIME_VALUE"] > 3000) & ~_u & ~_h)
    fired = [
        ("Churn &gt; 0.5 + Failed Pay", int(_u.sum()), RED),
        ("Churn &gt; 0.4 + Complaint", int(_h.sum()), INK),
        ("1 Policy + LTV &gt; 3000", int(_m.sum()), YELLOW),
        ("Standard Cycle", total - int(_u.sum()) - int(_h.sum()) - int(_m.sum()), MUTED),
    ]
    rows = "".join(
        f'<div class="bh-kv"><span class="bh-kv-k">{k}</span>'
        f'<span class="bh-kv-v" style="color:{c}">{v:,}</span></div>'
        for k, v, c in fired)
    st.html('<div class="bh-box"><div class="bh-box-title">'
            '<span>Scenario 10 Rules Fired</span><span>Rows</span></div>'
            f'{rows}</div>')

with st.sidebar:
    st.button("Sync Snowflake", on_click=clear_all_caches,
              use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
