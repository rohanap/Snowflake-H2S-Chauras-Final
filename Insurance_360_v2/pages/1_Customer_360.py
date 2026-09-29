"""
Page 1 -- CUSTOMER 360 PROFILE   (Bauhaus / Neo-Brutalist)
Built from stitch_snowflake_streamlit_ui_redesign/customer_360_profile/

Mockup -> Streamlit mapping:
  * search row + risk filter    -> st.form so typing does not fire queries
  * identity card + badge cluster-> one st.html block
  * Predictive Risk Engine panel-> yellow box, hand-drawn hatched meter
                                   (no Plotly gauge; the brutalist meter is a
                                   div, which is cheaper and on-style)
  * 4 numbered signal cards     -> .bh-signal, one st.html block for all four
  * oversized NBA panel         -> yellow box with display-scale action text
  * AI script preview           -> .bh-mono block + regenerate in a fragment
  * source ledger tabs          -> st.segmented_control, so only the selected
                                   ledger queries
"""
import os
import sys
import time

import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import (  # noqa: E402
    clear_all_caches, generate_nba_message, load_all_customers_summary,
    load_customer_360, load_customer_claims, load_customer_confidence,
    load_customer_interactions, load_customer_payments, load_customer_policies,
    load_customer_transcripts,
)
from utils.theme import (  # noqa: E402
    BLUE, INK, RED, YELLOW, apply_theme, banner, inr, loading, section,
    sidebar, topbar,
)

st.set_page_config(page_title="Customer 360 // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

banner(
    "Customer 360 Profile",
    "Single-policyholder deep dive &mdash; identity, exposure, claim and payment "
    "signals, voice-of-customer sentiment, model scores and the dispatch-ready "
    "next best action.",
    eyebrow="Entity Resolution // Live Lookup",
)

_t0 = time.perf_counter()
with loading("Loading customer directory"):
    all_c = load_all_customers_summary()
_ms = int((time.perf_counter() - _t0) * 1000)

topbar(records=f"{len(all_c):,}", latency=f"{_ms} ms")

# ── Search ────────────────────────────────────────────────────
st.session_state.setdefault("c1_term", "")
st.session_state.setdefault("c1_risk", "All")


def _commit_search() -> None:
    st.session_state["c1_term"] = st.session_state["_c1_t"].strip()
    st.session_state["c1_risk"] = st.session_state["_c1_r"]


with st.form("c1_search", border=True):
    s1, s2, s3 = st.columns([3, 1, 1])
    with s1:
        st.text_input("Search Name Or Customer ID",
                      value=st.session_state["c1_term"],
                      placeholder="e.g. Rebecca Henderson  //  CUST00031",
                      key="_c1_t")
    with s2:
        _risks = ["All", "High", "Medium", "Low"]
        st.selectbox("Churn Tier", _risks,
                     index=_risks.index(st.session_state["c1_risk"]),
                     key="_c1_r")
    with s3:
        st.write("")
        st.form_submit_button("Resolve", type="primary",
                              on_click=_commit_search,
                              use_container_width=True)

filtered = all_c
if st.session_state["c1_term"]:
    t = st.session_state["c1_term"]
    filtered = filtered[
        filtered["NAME"].str.contains(t, case=False, na=False)
        | filtered["CUSTOMER_ID"].str.contains(t, case=False, na=False)
    ]
if st.session_state["c1_risk"] != "All":
    filtered = filtered[filtered["CHURN_RISK_LABEL"] == st.session_state["c1_risk"]]

if filtered.empty:
    st.warning("No policyholder matches that query.")
    st.stop()

_labels = (filtered["NAME"] + "  //  " + filtered["CUSTOMER_ID"]
           + "  //  " + filtered["CITY"] + ", " + filtered["STATE"])
name_map = dict(zip(_labels, filtered["CUSTOMER_ID"]))

st.caption(f"{len(name_map):,} match(es) resolved")
sel = st.selectbox("Select Entity", list(name_map.keys()), key="c1_sel")
cid = name_map[sel]

with loading("Assembling 360 profile"):
    row = load_customer_360(cid)

if row is None:
    st.error("Could not load customer data.")
    st.stop()

pri = str(row["NBA_PRIORITY"])
risk = str(row["CHURN_RISK_LABEL"])
churn_pct = round(float(row["CHURN_RISK_SCORE"]) * 100, 1)
upsell_pct = round(float(row["UPSELL_PROBABILITY"] or 0) * 100)
sent = float(row["AVG_SENTIMENT_SCORE"] or 0)

# ── Identity card ─────────────────────────────────────────────
section("Entity Record", "01")

_badges = "".join([
    f'<span class="bh-chip {"red" if pri == "Urgent" else "yellow" if pri in ("High", "Medium") else "ghost"}">{pri} Priority</span>',
    f'<span class="bh-chip {"redsoft" if risk == "High" else "ghost"}">{risk} Churn</span>',
    f'<span class="bh-chip bluesoft">{row["SEGMENT"]}</span>',
    f'<span class="bh-chip dark">{row["CUSTOMER_ID"]}</span>',
])

_facts = [
    ("Segment", row["SEGMENT"]),
    ("Income Band", row["INCOME_BAND"]),
    ("Tenure", f"{int(row['TENURE_DAYS'])} d"),
    ("Age Group", f"{row['AGE_GROUP']} / {row['AGE']}"),
    ("Since", str(row["CUSTOMER_SINCE"])[:10]),
    ("Channel", row["PRIMARY_CHANNEL"]),
]
_facts_html = "".join(
    f'<div class="bh-fact"><div class="bh-fact-k">{k}</div>'
    f'<div class="bh-fact-v">{v}</div></div>' for k, v in _facts)

id_col, risk_col = st.columns([1.55, 1])

with id_col:
    st.html(f"""
    <div class="bh-box" style="padding:0">
        <div style="padding:18px 20px">
            <div style="margin-bottom:12px">{_badges}</div>
            <div style="font-family:var(--font-display);font-weight:900;
                        font-size:clamp(1.7rem,3.6vw,2.9rem);line-height:0.92;
                        letter-spacing:-0.045em;text-transform:uppercase;
                        color:var(--ink)">{row['NAME']}</div>
            <div style="font-family:var(--font-mono);font-size:0.7rem;
                        font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                        color:var(--muted);margin-top:8px">
                {row['CITY']}, {row['STATE']}
            </div>
            <div style="display:flex;align-items:baseline;gap:12px;margin-top:16px">
                <span style="font-family:var(--font-mono);font-size:0.6rem;
                             font-weight:700;letter-spacing:0.14em;
                             text-transform:uppercase;color:var(--muted)">
                    Customer Lifetime Value</span>
                <span style="font-family:var(--font-display);font-weight:900;
                             font-size:clamp(1.4rem,2.6vw,2.1rem);
                             letter-spacing:-0.035em;color:var(--ink)">
                    {inr(row['LIFETIME_VALUE'])}</span>
            </div>
        </div>
        <div class="bh-facts">{_facts_html}</div>
    </div>""")

with risk_col:
    _clr = RED if churn_pct > 65 else YELLOW if churn_pct > 35 else INK
    st.html(f"""
    <div class="bh-box yellow">
        <div class="bh-box-title" style="border-bottom-color:var(--ink)">
            <span>Predictive Risk Engine</span><span>XGBoost</span></div>
        <div style="font-family:var(--font-mono);font-size:0.6rem;font-weight:700;
                    letter-spacing:0.14em;text-transform:uppercase">
            Churn Probability</div>
        <div style="font-family:var(--font-display);font-weight:900;
                    font-size:clamp(2.6rem,5.6vw,4.2rem);line-height:0.88;
                    letter-spacing:-0.05em;color:var(--ink);margin:4px 0 10px 0">
            {churn_pct}%</div>
        <div class="bh-meter {'red' if churn_pct > 65 else ''}">
            <i style="width:{max(2, min(100, churn_pct))}%"></i></div>
        <div class="bh-meter-scale"><span>0</span><span>35 LOW</span>
            <span>65 HIGH</span><span>100</span></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0;
                    margin-top:16px;border-top:2px solid var(--ink)">
            <div style="padding:11px 12px;border-right:2px solid var(--ink)">
                <div class="bh-fact-k">Upsell Propensity</div>
                <div class="bh-fact-v">{upsell_pct}%</div></div>
            <div style="padding:11px 12px">
                <div class="bh-fact-k">Risk Tier</div>
                <div class="bh-fact-v" style="color:{_clr}">{risk}</div></div>
        </div>
        <div style="font-family:var(--font-mono);font-size:0.56rem;font-weight:700;
                    letter-spacing:0.1em;text-transform:uppercase;
                    color:var(--muted);margin-top:12px;
                    border-top:1px dashed var(--ink);padding-top:9px">
            Model: XGBoost // Features: policy, claim, payment, voice
        </div>
    </div>""")

# ── Signal cards ──────────────────────────────────────────────
section("Signal Decomposition", "02")


def _signal(num: str, title: str, rows: list, alert: bool) -> str:
    body = "".join(
        f'<div class="bh-kv"><span class="bh-kv-k">{k}</span>'
        f'<span class="bh-kv-v">{v}</span></div>' for k, v in rows)
    return (f'<div class="bh-signal {"alert" if alert else "ok"}">'
            f'<div class="bh-signal-h"><span class="bh-signal-n">{num}</span>'
            f'<span class="bh-signal-t">{title}</span></div>'
            f'<div class="bh-signal-b">{body}</div></div>')


_signals = [
    _signal("01", "Policy", [
        ("Active", int(row["ACTIVE_POLICY_COUNT"])),
        ("Types", int(row["ACTIVE_POLICY_TYPE_COUNT"])),
        ("Premium", inr(row["TOTAL_ACTIVE_PREMIUM"])),
        ("Lapsed", int(row["LAPSED_CANCELLED_COUNT"])),
        ("Days To Expiry", int(row["DAYS_TO_NEAREST_EXPIRY"] or 0)),
    ], int(row["LAPSED_CANCELLED_COUNT"]) > 0),
    _signal("02", "Claim", [
        ("Total", int(row["TOTAL_CLAIMS"])),
        ("Open", int(row["OPEN_CLAIMS"])),
        ("Approved", int(row["APPROVED_CLAIMS"])),
        ("Rejected", int(row["REJECTED_CLAIMS"])),
        ("Avg Amount", inr(row["AVG_CLAIM_AMOUNT"])),
    ], int(row["OPEN_CLAIMS"]) > 0),
    _signal("03", "Payment", [
        ("Total", int(row["TOTAL_PAYMENTS"])),
        ("Failed", int(row["FAILED_PAYMENT_COUNT"])),
        ("Pending", int(row["PENDING_PAYMENT_COUNT"])),
        ("Fail Rate", f"{float(row['FAILED_PAYMENT_RATE_PCT'] or 0):.1f}%"),
        ("Total Paid", inr(row["TOTAL_PAID"])),
    ], int(row["FAILED_PAYMENT_COUNT"]) > 0),
    _signal("04", "Voice", [
        ("Calls", int(row["TOTAL_CALLS"])),
        ("Avg Sentiment", f"{sent:+.3f}"),
        ("Complaints", int(row["COMPLAINT_COUNT"])),
        ("Last Intent", str(row["LAST_CUSTOMER_INTENT"] or "—").replace("_", " ").title()),
        ("Cancel Risk", int(row["CANCELLATION_RISK_CALL_COUNT"])),
    ], sent < -0.3),
]
st.html('<div class="bh-bento" style="grid-template-columns:'
        'repeat(auto-fit,minmax(235px,1fr))">' + "".join(_signals) + "</div>")

# ── Next Best Action ──────────────────────────────────────────
section("Next Best Action // Scenario 10", "03")

conf_score, conf_explain = load_customer_confidence(cid)
_conf_pct = round((conf_score or 0) * 100)
_conf_clr = YELLOW if _conf_pct >= 50 else RED

st.html(f"""
<div class="bh-box yellow">
    <div class="bh-box-title" style="border-bottom-color:var(--ink)">
        <span>Recommended Intervention</span>
        <span>{pri} // {row['NBA_CHANNEL']}</span></div>
    <div style="font-family:var(--font-display);font-weight:900;
                font-size:clamp(1.5rem,4vw,3rem);line-height:0.92;
                letter-spacing:-0.045em;text-transform:uppercase;color:var(--ink)">
        {row['NBA_ACTION']}</div>
    <p class="bh-sub" style="border-left-color:var(--ink);margin-top:14px">
        {row['NBA_REASON']}</p>
    <div class="bh-facts" style="margin-top:18px;border-top-color:var(--ink)">
        <div class="bh-fact"><div class="bh-fact-k">Dispatch Channel</div>
            <div class="bh-fact-v">{row['NBA_CHANNEL']}</div></div>
        <div class="bh-fact"><div class="bh-fact-k">Churn Risk</div>
            <div class="bh-fact-v">{churn_pct}%</div></div>
        <div class="bh-fact"><div class="bh-fact-k">Value At Risk</div>
            <div class="bh-fact-v">{inr(row['LIFETIME_VALUE'])}</div></div>
        <div class="bh-fact"><div class="bh-fact-k">Failed Payments</div>
            <div class="bh-fact-v" style="color:{RED if int(row['FAILED_PAYMENT_COUNT']) else INK}">
                {int(row['FAILED_PAYMENT_COUNT'])}</div></div>
        <div class="bh-fact"><div class="bh-fact-k">NBA Confidence</div>
            <div class="bh-fact-v" style="color:{_conf_clr}">{_conf_pct}%</div></div>
    </div>
</div>""")

if conf_explain:
    st.html(f'<div class="bh-box tight"><div class="bh-box-title">'
            f'<span>Confidence Signal</span><span>{_conf_pct}%</span></div>'
            f'<div class="bh-meter {"red" if _conf_pct < 50 else ""}">'
            f'<i style="width:{max(2, _conf_pct)}%"></i></div>'
            f'<div style="font-family:var(--font-body);font-size:0.84rem;'
            f'line-height:1.6;color:var(--muted);margin-top:10px">'
            f'{conf_explain}</div></div>')


from pages._email_helpers import dispatch_emails as _dispatch_emails


@st.fragment
def agent_script() -> None:
    """Isolated so regenerating never rebuilds the whole profile."""
    st.html('<div class="bh-box-title"><span>AI Agent Script Preview</span>'
            '<span>Cortex Complete // mistral-large3</span></div>')
    pre = str(row.get("NBA_MESSAGE") or "").strip()
    if len(pre) > 20:
        st.html(f'<div class="bh-mono">{pre}</div>')
        st.caption("Use the copy control on the block below to lift the script.")
        st.code(pre, language="text")
    else:
        st.info("No pre-generated script for this policyholder.")

    a1, a2 = st.columns(2)
    with a1:
        if st.button("Regenerate Script", key="c1_regen",
                     use_container_width=True):
            with loading("Cortex Complete drafting"):
                msg = generate_nba_message(row)
            st.html(f'<div class="bh-mono dark">{msg}</div>')
            st.code(msg, language="text")
    with a2:
        if st.button("Dispatch Email", key="c1_dispatch", type="primary",
                     use_container_width=True):
            script_body = str(row.get("NBA_MESSAGE") or "").strip()
            if len(script_body) <= 20:
                script_body = f"Action: {row['NBA_ACTION']}\nReason: {row['NBA_REASON']}"
            try:
                with loading("Sending emails via Snowflake"):
                    internal_to, customer_to = _dispatch_emails(row, script_body)
                st.success(
                    f"2 emails dispatched:\n\n"
                    f"**Internal team** (full details) -> {internal_to}\n\n"
                    f"**Customer** (HTML email) -> {customer_to}"
                )
            except Exception as e:
                st.error(f"Email dispatch failed: {e}")


agent_script()

# ── Recurring themes (AI_AGG) ─────────────────────────────────
_themes = str(row.get("RECURRING_THEMES") or "").strip()
if _themes:
    section("Synthesised Call Themes // AI_AGG", "04")
    st.html(
        '<div class="bh-box blue"><div class="bh-box-title">'
        f'<span>Aggregated From {int(row["TOTAL_CALLS"])} Calls</span>'
        '<span>AI_AGG()</span></div>'
        f'<div style="font-family:var(--font-body);font-size:0.88rem;'
        f'line-height:1.7;color:var(--ink)">{_themes}</div></div>')

# ── Source ledgers ────────────────────────────────────────────
section("Source Ledgers", "05")

LEDGERS = ["Policies", "Claims", "Payments", "Interactions", "Transcripts"]
ledger = st.segmented_control("Ledger", LEDGERS, default=LEDGERS[0],
                              key="c1_ledger",
                              label_visibility="collapsed") or LEDGERS[0]

if ledger == "Policies":
    with loading("Reading policy ledger"):
        d = load_customer_policies(cid)
    if d.empty:
        st.info("No policies on record.")
    else:
        st.dataframe(d, use_container_width=True, hide_index=True)
elif ledger == "Claims":
    with loading("Reading claim ledger"):
        d = load_customer_claims(cid)
    if d.empty:
        st.info("No claims on record.")
    else:
        st.dataframe(d, use_container_width=True, hide_index=True)
elif ledger == "Payments":
    with loading("Reading payment ledger"):
        d = load_customer_payments(cid)
    if d.empty:
        st.info("No payments on record.")
    else:
        d = d.copy()
        d["FLAG"] = d["PAYMENT_STATUS"].map(
            {"Completed": "OK", "Failed": "FAIL", "Pending": "WAIT"}).fillna("—")
        st.dataframe(d, use_container_width=True, hide_index=True)
elif ledger == "Interactions":
    with loading("Reading interaction ledger"):
        d = load_customer_interactions(cid)
    if d.empty:
        st.info("No interactions on record.")
    else:
        st.dataframe(d, use_container_width=True, hide_index=True)
else:
    with loading("Reading transcript ledger"):
        tr = load_customer_transcripts(cid)
    if tr.empty:
        st.info("No transcripts on record.")
    else:
        cards = []
        for _, t in tr.head(3).iterrows():
            s = float(t["SENTIMENT_SCORE"] or 0)
            tone = "red" if s < -0.3 else "yellow" if s < 0.1 else "ghost"
            intent = str(t["CUSTOMER_INTENT"] or "unknown").replace("_", " ").title()
            cards.append(f"""
            <div class="bh-box tight">
                <div class="bh-box-title">
                    <span>{str(t['INTERACTION_DATE'])[:10]} // {t['CHANNEL']}</span>
                    <span style="color:{RED if s < -0.3 else INK}">{round(s, 2)} sentiment</span>
                </div>
                <div style="margin-bottom:9px">
                    <span class="bh-chip {tone}">{intent}</span>
                    <span class="bh-chip ghost">{str(t['RESOLUTION_FLAG']).strip().title()}</span>
                </div>
                <div class="bh-kv"><span class="bh-kv-k">Subject</span>
                    <span class="bh-kv-v">{t['SUBJECT']}</span></div>
                <div style="font-family:var(--font-body);font-size:0.82rem;
                            line-height:1.6;color:var(--muted);margin-top:9px">
                    {t['CALL_SUMMARY']}</div>
                <div style="font-family:var(--font-mono);font-size:0.62rem;
                            font-weight:700;text-transform:uppercase;
                            color:{BLUE};margin-top:9px">
                    Topics: {t['KEY_TOPICS']}</div>
            </div>""")
        st.html("".join(cards))

        tx_map = {f"{str(t['INTERACTION_DATE'])[:10]} // {t['CALL_ID']}": i
                  for i, t in tr.head(3).iterrows()}
        if st.toggle("Open Full Transcript", key="c1_tx_toggle"):
            pick = st.selectbox("Call", list(tx_map.keys()), key="c1_tx_pick")
            st.html('<div class="bh-mono">'
                    f'{tr.loc[tx_map[pick], "TRANSCRIPT_TEXT"]}</div>')

with st.sidebar:
    st.button("Sync Snowflake", on_click=clear_all_caches,
              use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
