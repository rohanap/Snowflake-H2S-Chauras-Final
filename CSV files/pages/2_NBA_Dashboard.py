"""
Page 2 — NBA Priority Dashboard
Scenario 10 triage list · Priority charts · Live outreach generation
"""
import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import load_all_360, generate_nba_message
from utils.theme import apply_theme

st.set_page_config(page_title="NBA Dashboard", page_icon="📋", layout="wide")
apply_theme()
st.markdown("# 📋 NBA Priority Dashboard")
st.caption("Scenario 10 rules: Urgent = churn>0.5 + failed payment · High = churn>0.4 + complaint · Medium = single policy + LTV>3000")

df = load_all_360()

# ── KPI banner ────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("🔴 Urgent", int((df["NBA_PRIORITY"]=="Urgent").sum()))
c2.metric("🟠 High",   int((df["NBA_PRIORITY"]=="High").sum()))
c3.metric("🟡 Medium", int((df["NBA_PRIORITY"]=="Medium").sum()))
c4.metric("🟢 Low",    int((df["NBA_PRIORITY"]=="Low").sum()))
ltv_risk = df[df["CHURN_RISK_LABEL"]=="High"]["LIFETIME_VALUE"].sum()
c5.metric("💰 LTV at Risk", f"₹{ltv_risk:,.0f}")
st.divider()

# ── Filters ────────────────────────────────────────────────────
f1,f2,f3,f4 = st.columns(4)
with f1:
    pri_f  = st.multiselect("Priority", ["Urgent","High","Medium","Low"],
                             default=["Urgent","High"])
with f2:
    seg_f  = st.multiselect("Segment", sorted(df["SEGMENT"].unique()),
                             default=sorted(df["SEGMENT"].unique()))
with f3:
    ch_f   = st.multiselect("Channel", sorted(df["NBA_CHANNEL"].unique()),
                             default=sorted(df["NBA_CHANNEL"].unique()))
with f4:
    sort_by = st.selectbox("Sort by",
        ["Churn Risk ↓","LTV ↓","Failed Payments ↓","Complaints ↓"])

filt = df.copy()
if pri_f: filt = filt[filt["NBA_PRIORITY"].isin(pri_f)]
if seg_f: filt = filt[filt["SEGMENT"].isin(seg_f)]
if ch_f:  filt = filt[filt["NBA_CHANNEL"].isin(ch_f)]
sort_map = {
    "Churn Risk ↓":     ("CHURN_RISK_SCORE",     False),
    "LTV ↓":            ("LIFETIME_VALUE",         False),
    "Failed Payments ↓":("FAILED_PAYMENT_COUNT",   False),
    "Complaints ↓":     ("COMPLAINT_COUNT",         False),
}
sc, sa = sort_map[sort_by]
filt = filt.sort_values(sc, ascending=sa).reset_index(drop=True)

st.markdown(f'<p class="section-title">Triage List — {len(filt)} Customers</p>',
            unsafe_allow_html=True)

PRI_CLR = {"Urgent":"#E63946","High":"#FF6B35","Medium":"#FFB300","Low":"#2DC653"}

for _, row in filt.iterrows():
    pri  = row["NBA_PRIORITY"]
    pclr = PRI_CLR.get(pri, "#29B5E8")
    cs   = round(float(row["CHURN_RISK_SCORE"])*100, 1)
    sent = round(float(row["AVG_SENTIMENT_SCORE"]), 2)
    sclr = "#E63946" if sent < -0.3 else "#FFB300" if sent < 0.1 else "#2DC653"

    h1,h2,h3,h4,h5,h6,h7 = st.columns([2.2,0.9,0.9,0.9,0.9,0.9,1.4])

    with h1:
        st.markdown(f"""
        <div style='border-left:4px solid {pclr};padding-left:10px'>
            <b style='color:#F0F4F8'>{row['NAME']}</b>
            <span class='badge-{pri}' style='margin-left:6px;font-size:9px'>{pri}</span><br>
            <span style='color:#8FB0CC;font-size:10px'>
                {row['SEGMENT']} · {row['CITY']}, {row['STATE']} · {row['NBA_CHANNEL']}
            </span>
        </div>""", unsafe_allow_html=True)

    with h2:
        st.markdown(f"""
        <div style='text-align:center'>
            <div style='font-size:17px;font-weight:700;color:{pclr}'>{cs}%</div>
            <div style='font-size:9px;color:#8FB0CC'>CHURN</div>
        </div>""", unsafe_allow_html=True)

    with h3:
        st.markdown(f"""
        <div style='text-align:center'>
            <div style='font-size:13px;font-weight:700;color:#F0F4F8'>
                ₹{row['LIFETIME_VALUE']:,.0f}
            </div>
            <div style='font-size:9px;color:#8FB0CC'>LTV</div>
        </div>""", unsafe_allow_html=True)

    with h4:
        fc   = int(row["FAILED_PAYMENT_COUNT"])
        fclr = "#E63946" if fc > 0 else "#2DC653"
        st.markdown(f"""
        <div style='text-align:center'>
            <div style='font-size:17px;font-weight:700;color:{fclr}'>{fc}</div>
            <div style='font-size:9px;color:#8FB0CC'>FAILED PAY</div>
        </div>""", unsafe_allow_html=True)

    with h5:
        cc   = int(row["COMPLAINT_COUNT"])
        cclr = "#E63946" if cc > 0 else "#2DC653"
        st.markdown(f"""
        <div style='text-align:center'>
            <div style='font-size:17px;font-weight:700;color:{cclr}'>{cc}</div>
            <div style='font-size:9px;color:#8FB0CC'>COMPLAINTS</div>
        </div>""", unsafe_allow_html=True)

    with h6:
        st.markdown(f"""
        <div style='text-align:center'>
            <div style='font-size:17px;font-weight:700;color:{sclr}'>{sent}</div>
            <div style='font-size:9px;color:#8FB0CC'>SENTIMENT</div>
        </div>""", unsafe_allow_html=True)

    with h7:
        with st.expander("✉️ Outreach"):
            st.markdown(f"**Action:** {row['NBA_ACTION']}")
            pre = str(row.get("NBA_MESSAGE","")).strip()
            if pre and len(pre) > 20:
                st.markdown(f"""
                <div class='ai-box' style='padding:10px'>
                    <p style='color:#E8EDF2;font-size:12px;margin:0'>{pre}</p>
                </div>""", unsafe_allow_html=True)
                st.code(pre, language="")
            if st.button("Regenerate", key=f"regen_{row['CUSTOMER_ID']}"):
                with st.spinner("Generating…"):
                    msg = generate_nba_message(row)
                    st.code(msg, language="")

    w = max(2, round(float(row["CHURN_RISK_SCORE"])*100))
    st.markdown(f"""
    <div style='background:#1E3A5F;border-radius:3px;height:3px;margin:4px 0 10px 0'>
        <div style='width:{w}%;background:{pclr};height:3px;border-radius:3px'></div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Charts ─────────────────────────────────────────────────────
st.markdown('<p class="section-title">Priority Distribution</p>', unsafe_allow_html=True)
cl, cr = st.columns(2)

with cl:
    pri_cnt = df["NBA_PRIORITY"].value_counts().reindex(
        ["Urgent","High","Medium","Low"], fill_value=0)
    fig = go.Figure(go.Bar(
        x=pri_cnt.index, y=pri_cnt.values,
        marker_color=["#E63946","#FF6B35","#FFB300","#2DC653"],
        text=pri_cnt.values, textposition="outside"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E8EDF2", showlegend=False, title="Customers by NBA Priority",
        yaxis=dict(gridcolor="#1E3A5F"), margin=dict(t=40,b=20,l=10,r=10))
    st.plotly_chart(fig, use_container_width=True)

with cr:
    ltv_pri = df.groupby("NBA_PRIORITY")["LIFETIME_VALUE"].sum().reindex(
        ["Urgent","High","Medium","Low"], fill_value=0)
    fig2 = go.Figure(go.Bar(
        x=ltv_pri.index, y=ltv_pri.values,
        marker_color=["#E63946","#FF6B35","#FFB300","#2DC653"],
        text=[f"₹{v:,.0f}" for v in ltv_pri.values], textposition="outside"))
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E8EDF2", showlegend=False, title="LTV at Stake by Priority",
        yaxis=dict(gridcolor="#1E3A5F", title="₹ LTV"),
        margin=dict(t=40,b=20,l=10,r=10))
    st.plotly_chart(fig2, use_container_width=True)

# Scenario 10 rule breakdown
st.markdown('<p class="section-title">Scenario 10 Rule Breakdown</p>',
            unsafe_allow_html=True)
r1 = len(df[(df["CHURN_RISK_SCORE"]>0.5) & (df["FAILED_PAYMENT_COUNT"]>0)])
r2 = len(df[(df["CHURN_RISK_SCORE"]>0.4) & (df["COMPLAINT_COUNT"]>0) &
            ~((df["CHURN_RISK_SCORE"]>0.5) & (df["FAILED_PAYMENT_COUNT"]>0))])
r3 = len(df[(df["ACTIVE_POLICY_TYPE_COUNT"]==1) & (df["LIFETIME_VALUE"]>3000) &
            ~((df["CHURN_RISK_SCORE"]>0.5) & (df["FAILED_PAYMENT_COUNT"]>0)) &
            ~((df["CHURN_RISK_SCORE"]>0.4) & (df["COMPLAINT_COUNT"]>0))])
r4 = len(df) - r1 - r2 - r3

fig3 = go.Figure(go.Bar(
    x=["Urgent: Churn>0.5\n+ Failed Payment","High: Churn>0.4\n+ Complaint",
       "Medium: 1 Policy\n+ LTV>3000","Low:\nStandard"],
    y=[r1,r2,r3,r4],
    marker_color=["#E63946","#FF6B35","#FFB300","#2DC653"],
    text=[r1,r2,r3,r4], textposition="outside"))
fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#E8EDF2", showlegend=False,
    yaxis=dict(gridcolor="#1E3A5F"), margin=dict(t=20,b=20,l=10,r=10))
st.plotly_chart(fig3, use_container_width=True)

with st.expander("📋 Export filtered table"):
    cols = ["CUSTOMER_ID","NAME","SEGMENT","STATE","CHURN_RISK_LABEL",
            "CHURN_RISK_SCORE","LIFETIME_VALUE","FAILED_PAYMENT_COUNT",
            "COMPLAINT_COUNT","OPEN_CLAIMS","NBA_PRIORITY","NBA_ACTION","NBA_CHANNEL"]
    st.dataframe(filt[[c for c in cols if c in filt.columns]],
                 use_container_width=True, hide_index=True)
