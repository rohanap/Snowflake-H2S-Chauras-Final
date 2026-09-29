"""
Page 1 — Customer 360 Profile
Search → Identity → Policies → Claims → Payments → VOC → NBA → AI message
"""
import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import (
    load_all_customers_summary, load_customer_360,
    load_customer_policies, load_customer_claims,
    load_customer_payments, load_customer_interactions,
    load_customer_transcripts, generate_nba_message,
)
from utils.theme import apply_theme
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Customer 360", page_icon="👤", layout="wide")
apply_theme()
session = get_active_session()
st.markdown("# 👤 Customer 360 Profile")
st.caption("Search any policyholder to see their full 360 view and personalised Next Best Action.")

# ── Search ────────────────────────────────────────────────────
all_c = load_all_customers_summary()
f1, f2 = st.columns([3,1])
with f1:
    term = st.text_input("🔍 Search by name or customer ID",
                         placeholder="e.g. Rajesh Sharma or CUST0001")
with f2:
    risk_f = st.selectbox("Filter risk", ["All","High","Medium","Low"])

filtered = all_c.copy()
if term:
    m = (all_c["NAME"].str.contains(term, case=False) |
         all_c["CUSTOMER_ID"].str.contains(term, case=False))
    filtered = all_c[m]
if risk_f != "All":
    filtered = filtered[filtered["CHURN_RISK_LABEL"] == risk_f]

name_map = {
    f"{r['NAME']} ({r['CUSTOMER_ID']}) — {r['CITY']}, {r['STATE']} · {r['SEGMENT']}":
    r["CUSTOMER_ID"]
    for _, r in filtered.iterrows()
}
if not name_map:
    st.warning("No customers match your search.")
    st.stop()

sel   = st.selectbox("Select customer", list(name_map.keys()))
cid   = name_map[sel]
row   = load_customer_360(cid)
if row is None:
    st.error("Could not load customer data.")
    st.stop()

st.divider()

# ── Identity card + Churn gauge ───────────────────────────────
id_col, gauge_col = st.columns([2.5,1])
with id_col:
    pri  = row["NBA_PRIORITY"]
    risk = row["CHURN_RISK_LABEL"]
    st.markdown(f"""
    <div style='background:#0D1B2A;border:1px solid #1E3A5F;
                border-radius:10px;padding:20px'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start'>
            <div>
                <h2 style='color:#F0F4F8;margin:0'>{row['NAME']}</h2>
                <p style='color:#8FB0CC;margin:4px 0'>{row['CITY']}, {row['STATE']}</p>
            </div>
            <div>
                <span class='badge-{pri}'>{pri}</span>&nbsp;
                <span class='badge-{risk}-risk'>{risk} Risk</span>
            </div>
        </div>
        <hr style='border-color:#1E3A5F;margin:12px 0'>
        <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:10px'>
            <div><span style='color:#8FB0CC;font-size:10px'>SEGMENT</span><br>
                 <b>{row['SEGMENT']}</b></div>
            <div><span style='color:#8FB0CC;font-size:10px'>INCOME BAND</span><br>
                 <b>{row['INCOME_BAND']}</b></div>
            <div><span style='color:#8FB0CC;font-size:10px'>TENURE</span><br>
                 <b>{row['TENURE_DAYS']} days</b></div>
            <div><span style='color:#8FB0CC;font-size:10px'>AGE GROUP</span><br>
                 <b>{row['AGE_GROUP']} (Age {row['AGE']})</b></div>
            <div><span style='color:#8FB0CC;font-size:10px'>CUSTOMER SINCE</span><br>
                 <b>{str(row['CUSTOMER_SINCE'])[:10]}</b></div>
            <div><span style='color:#8FB0CC;font-size:10px'>LIFETIME VALUE</span><br>
                 <b>₹{row['LIFETIME_VALUE']:,.0f}</b></div>
            <div><span style='color:#8FB0CC;font-size:10px'>PRIMARY CHANNEL</span><br>
                 <b>{row['PRIMARY_CHANNEL']}</b></div>
            <div><span style='color:#8FB0CC;font-size:10px'>CUSTOMER ID</span><br>
                 <b>{row['CUSTOMER_ID']}</b></div>
        </div>
    </div>""", unsafe_allow_html=True)

with gauge_col:
    cs   = round(float(row["CHURN_RISK_SCORE"])*100, 1)
    clr  = "#E63946" if cs > 65 else "#FFB300" if cs > 35 else "#2DC653"
    fig  = go.Figure(go.Indicator(
        mode="gauge+number", value=cs,
        number={"suffix":"%","font":{"color":clr,"size":32}},
        title={"text":"Churn Risk","font":{"color":"#8FB0CC","size":12}},
        gauge={
            "axis":{"range":[0,100],"tickcolor":"#8FB0CC",
                    "tickfont":{"color":"#8FB0CC"}},
            "bar":{"color":clr}, "bgcolor":"#1E3A5F",
            "steps":[{"range":[0,35],"color":"#0D2A1A"},
                     {"range":[35,65],"color":"#3A2A00"},
                     {"range":[65,100],"color":"#3A1010"}],
        }))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
                      margin=dict(t=40,b=10,l=20,r=20), height=200)
    st.plotly_chart(fig, use_container_width=True)
    c1,c2 = st.columns(2)
    c1.metric("LTV", f"₹{row['LIFETIME_VALUE']:,.0f}")
    c2.metric("Upsell", f"{round(row['UPSELL_PROBABILITY']*100)}%")

st.divider()

# ── Signal tiles ──────────────────────────────────────────────
st.markdown('<p class="section-title">360 Signals</p>', unsafe_allow_html=True)
s1,s2,s3,s4 = st.columns(4)

def tile(col, title, rows, accent="#29B5E8"):
    inner = "".join(
        f"<tr><td style='color:#8FB0CC;font-size:10px;padding:3px 0'>{k}</td>"
        f"<td style='color:#F0F4F8;font-size:10px;text-align:right'><b>{v}</b></td></tr>"
        for k,v in rows)
    col.markdown(f"""
    <div style='background:#0D1B2A;border:1px solid {accent};
                border-radius:8px;padding:12px'>
        <p style='color:{accent};font-size:10px;font-weight:700;
                  margin:0 0 8px 0;letter-spacing:1px'>{title}</p>
        <table style='width:100%'>{inner}</table>
    </div>""", unsafe_allow_html=True)

tile(s1,"POLICY SIGNALS",[
    ("Active Policies",   int(row["ACTIVE_POLICY_COUNT"])),
    ("Policy Types",      int(row["ACTIVE_POLICY_TYPE_COUNT"])),
    ("Active Premium",    f"₹{row['TOTAL_ACTIVE_PREMIUM']:,.0f}"),
    ("Lapsed/Cancelled",  int(row["LAPSED_CANCELLED_COUNT"])),
    ("Days to Expiry",    int(row["DAYS_TO_NEAREST_EXPIRY"])),
],"#29B5E8")

clr_c = "#E63946" if row["OPEN_CLAIMS"]>0 else "#2DC653"
tile(s2,"CLAIM SIGNALS",[
    ("Total Claims",      int(row["TOTAL_CLAIMS"])),
    ("Open Claims",       int(row["OPEN_CLAIMS"])),
    ("Approved Claims",   int(row["APPROVED_CLAIMS"])),
    ("Rejected Claims",   int(row["REJECTED_CLAIMS"])),
    ("Avg Amount",        f"₹{row['AVG_CLAIM_AMOUNT']:,.0f}"),
],clr_c)

clr_p = "#E63946" if row["FAILED_PAYMENT_COUNT"]>0 else "#2DC653"
tile(s3,"PAYMENT SIGNALS",[
    ("Total Payments",    int(row["TOTAL_PAYMENTS"])),
    ("Failed Payments",   int(row["FAILED_PAYMENT_COUNT"])),
    ("Pending Payments",  int(row["PENDING_PAYMENT_COUNT"])),
    ("Fail Rate",         f"{row['FAILED_PAYMENT_RATE_PCT']:.1f}%"),
    ("Total Paid",        f"₹{row['TOTAL_PAID']:,.0f}"),
],clr_p)

clr_s = "#E63946" if row["AVG_SENTIMENT_SCORE"]<-0.3 else \
        "#FFB300" if row["AVG_SENTIMENT_SCORE"]<0.1 else "#2DC653"
tile(s4,"VOICE OF CUSTOMER",[
    ("Total Calls",       int(row["TOTAL_CALLS"])),
    ("Avg Sentiment",     round(row["AVG_SENTIMENT_SCORE"],3)),
    ("Complaints",        int(row["COMPLAINT_COUNT"])),
    ("Last Intent",       (row["LAST_CUSTOMER_INTENT"] or "—").replace("_"," ").title()),
    ("Cancel Risk Calls", int(row["CANCELLATION_RISK_CALL_COUNT"])),
],clr_s)

st.divider()

# ── Source tables as tabs ─────────────────────────────────────
t1,t2,t3,t4 = st.tabs(["📋 Policies","📄 Claims","💳 Payments","📞 Interactions"])

with t1:
    pol_df = load_customer_policies(cid)
    if pol_df.empty:
        st.info("No policies found.")
    else:
        st.dataframe(pol_df, use_container_width=True, hide_index=True)

with t2:
    clm_df = load_customer_claims(cid)
    if clm_df.empty:
        st.info("No claims found.")
    else:
        st.dataframe(clm_df, use_container_width=True, hide_index=True)

with t3:
    pay_df = load_customer_payments(cid)
    if pay_df.empty:
        st.info("No payments found.")
    else:
        STATUS_COLOR = {"Completed":"🟢","Failed":"🔴","Pending":"🟡"}
        pay_df[""] = pay_df["PAYMENT_STATUS"].map(STATUS_COLOR).fillna("⚪")
        st.dataframe(pay_df, use_container_width=True, hide_index=True)

with t4:
    int_df = load_customer_interactions(cid)
    if int_df.empty:
        st.info("No interactions found.")
    else:
        st.dataframe(int_df, use_container_width=True, hide_index=True)

st.divider()

# ── Recurring themes (AI_AGG) ─────────────────────────────────
if row.get("RECURRING_THEMES"):
    st.markdown('<p class="section-title">🤖 AI-Synthesised Call Themes (AI_AGG)</p>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div class='ai-box'>
        <p style='color:#8FB0CC;font-size:10px;margin:0 0 6px 0'>
            Synthesised from {int(row['TOTAL_CALLS'])} calls via Snowflake AI_AGG()
        </p>
        <p style='color:#E8EDF2;line-height:1.7;margin:0'>{row['RECURRING_THEMES']}</p>
    </div>""", unsafe_allow_html=True)
    st.divider()

# ── Recent transcripts ────────────────────────────────────────
st.markdown('<p class="section-title">Recent Call Summaries</p>',
            unsafe_allow_html=True)
tr_df = load_customer_transcripts(cid)
if tr_df.empty:
    st.info("No transcript data available.")
else:
    for _, t in tr_df.head(3).iterrows():
        sent  = float(t["SENTIMENT_SCORE"] or 0)
        s_clr = "#E63946" if sent<-0.3 else "#FFB300" if sent<0.1 else "#2DC653"
        intent = (t["CUSTOMER_INTENT"] or "unknown").replace("_"," ").title()
        with st.expander(
            f"📞 {str(t['INTERACTION_DATE'])[:10]}  ·  {t['CHANNEL']}  ·  "
            f"{intent}  ·  Sentiment: {round(sent,2)}"
        ):
            c1,c2 = st.columns([1,2])
            c1.metric("Sentiment",  round(sent,3))
            c1.metric("Resolved",   str(t["RESOLUTION_FLAG"]).strip().title())
            c2.markdown(f"**Subject:** {t['SUBJECT']}")
            c2.markdown(f"**Summary:** {t['CALL_SUMMARY']}")
            c2.markdown(f"**Topics:**  {t['KEY_TOPICS']}")
            if st.checkbox("Show full transcript",
                           key=f"tr_{t['CALL_ID']}"):
                st.text_area("", t["TRANSCRIPT_TEXT"], height=150,
                             label_visibility="collapsed")

st.divider()

# ── NBA Box ────────────────────────────────────────────────────
st.markdown('<p class="section-title">🎯 Next Best Action — Scenario 10</p>',
            unsafe_allow_html=True)
PRI_CLR = {"Urgent":"#E63946","High":"#FF6B35","Medium":"#FFB300","Low":"#2DC653"}
pcl = PRI_CLR.get(row["NBA_PRIORITY"],"#29B5E8")

st.markdown(f"""
<div class='nba-box'>
    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px'>
        <span style='color:#29B5E8;font-size:11px;font-weight:700;letter-spacing:2px'>
            NEXT BEST ACTION
        </span>
        <span class='badge-{row["NBA_PRIORITY"]}'>{row["NBA_PRIORITY"]} PRIORITY</span>
    </div>
    <h4 style='color:#F0F4F8;margin:0 0 6px 0'>{row['NBA_ACTION']}</h4>
    <p style='color:#8FB0CC;font-size:12px;margin:0 0 14px 0'>{row['NBA_REASON']}</p>
    <div style='display:flex;gap:24px'>
        <div><span style='color:#8FB0CC;font-size:10px'>CHANNEL</span><br>
             <b style='color:#F0F4F8'>{row['NBA_CHANNEL']}</b></div>
        <div><span style='color:#8FB0CC;font-size:10px'>CHURN RISK</span><br>
             <b style='color:{pcl}'>{round(float(row['CHURN_RISK_SCORE'])*100,1)}%</b></div>
        <div><span style='color:#8FB0CC;font-size:10px'>LIFETIME VALUE</span><br>
             <b style='color:#F0F4F8'>₹{row['LIFETIME_VALUE']:,.0f}</b></div>
        <div><span style='color:#8FB0CC;font-size:10px'>FAILED PAYMENTS</span><br>
             <b style='color:{"#E63946" if row["FAILED_PAYMENT_COUNT"]>0 else "#2DC653"}'>
             {int(row['FAILED_PAYMENT_COUNT'])}</b></div>
    </div>
</div>""", unsafe_allow_html=True)

st.markdown('<p class="section-title" style="margin-top:16px">✉️ AI-Written Outreach Message</p>',
            unsafe_allow_html=True)
pre = str(row.get("NBA_MESSAGE","")).strip()
if pre and len(pre) > 20:
    st.markdown(f"""
    <div class='ai-box'>
        <p style='color:#8FB0CC;font-size:10px;margin:0 0 8px 0'>
            Cortex COMPLETE · mistral-large2
        </p>
        <p style='color:#E8EDF2;font-size:14px;line-height:1.8;margin:0'>{pre}</p>
    </div>""", unsafe_allow_html=True)
    if st.button("📋 Copy message", type="primary"):
        st.code(pre, language="")

if st.button("🔄 Regenerate with live Cortex AI"):
    with st.spinner("Generating…"):
        msg = generate_nba_message(row)
        st.markdown(f"""
        <div class='ai-box'>
            <p style='color:#FFB300;font-size:10px;margin:0 0 8px 0'>LIVE GENERATION</p>
            <p style='color:#E8EDF2;font-size:14px;line-height:1.8;margin:0'>{msg}</p>
        </div>""", unsafe_allow_html=True)
        st.code(msg, language="")
