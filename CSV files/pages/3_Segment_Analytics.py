"""
Page 3 — Segment Analytics
Scenarios 1, 4, 8, 9 · Churn by segment · Income band ·
Claim severity · Lapses by state · Channel effectiveness · Sentiment trend
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import (
    load_segment_analytics, load_sentiment_trend,
    load_claim_severity, load_lapses_by_state,
    load_channel_effectiveness, load_income_band_analysis,
    load_nba_distribution,
)
from utils.theme import apply_theme
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Segment Analytics", page_icon="📊", layout="wide")
apply_theme()
session = get_active_session()
st.markdown("# 📊 Segment Analytics")
st.caption("Churn risk, LTV, claim severity, lapses, and channel effectiveness — Scenarios 1, 4, 8 & 9.")

PAL = ["#29B5E8","#FFB300","#2DC653","#E63946","#9B5DE5","#F15BB5"]

seg_df  = load_segment_analytics()
sent_df = load_sentiment_trend()
clm_df  = load_claim_severity()
lap_df  = load_lapses_by_state()
ch_df   = load_channel_effectiveness()
inc_df  = load_income_band_analysis()
nba_df  = load_nba_distribution()

# ── Scenario tabs ──────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Churn by Segment",
    "📄 Scenario 4 — Claim Severity",
    "🗺 Scenario 8 — Lapses by State",
    "📞 Scenario 9 — Channel",
    "📈 Sentiment & NBA",
])

# ── Tab 1: Churn by Segment ────────────────────────────────────
with tab1:
    st.markdown('<p class="section-title">Scenario 1 — High-Value Customers at Churn Risk</p>',
                unsafe_allow_html=True)

    # Scenario 1 from Gold view
    sc1 = session.sql("""
        SELECT CUSTOMER_ID, NAME, SEGMENT, LIFETIME_VALUE,
               ROUND(CHURN_RISK_SCORE*100,1) AS CHURN_RISK_PCT,
               CHURN_RISK_LABEL, ACTIVE_POLICY_COUNT, NBA_PRIORITY
        FROM INSURANCE_C360.GOLD.CUSTOMER_360_VIEW
        WHERE CHURN_RISK_SCORE > 0.5 AND LIFETIME_VALUE > 5000
        ORDER BY LIFETIME_VALUE DESC, CHURN_RISK_SCORE DESC
        LIMIT 20
    """).to_pandas()

    if not sc1.empty:
        c1,c2 = st.columns([1.4,1])
        with c1:
            fig = go.Figure(go.Bar(
                x=sc1["NAME"].str.split().str[0],
                y=sc1["LIFETIME_VALUE"],
                marker_color=[
                    "#E63946" if v > 75 else "#FFB300" if v > 50 else "#29B5E8"
                    for v in sc1["CHURN_RISK_PCT"]],
                text=["₹"+f"{v:,.0f}" for v in sc1["LIFETIME_VALUE"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>LTV: ₹%{y:,.0f}<extra></extra>"))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
                title="High-LTV Customers at Churn Risk (LTV>₹5000, Churn>50%)",
                yaxis=dict(gridcolor="#1E3A5F", title="Lifetime Value (₹)"),
                xaxis=dict(tickangle=-30), margin=dict(t=40,b=60,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.dataframe(sc1[["NAME","SEGMENT","CHURN_RISK_PCT",
                               "LIFETIME_VALUE","NBA_PRIORITY"]],
                         use_container_width=True, hide_index=True)
    else:
        st.info("No high-value at-risk customers found in current data.")

    st.divider()
    st.markdown('<p class="section-title">Churn Risk & LTV by Segment</p>',
                unsafe_allow_html=True)
    cl, cr = st.columns(2)
    with cl:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Avg Churn %", x=seg_df["SEGMENT"],
            y=seg_df["AVG_CHURN_RISK_PCT"], marker_color="#E63946",
            text=seg_df["AVG_CHURN_RISK_PCT"].round(1).astype(str)+"%",
            textposition="outside"))
        fig2.add_trace(go.Scatter(name="High Risk Count", x=seg_df["SEGMENT"],
            y=seg_df["HIGH_RISK_COUNT"], mode="markers+lines", yaxis="y2",
            marker=dict(size=10,color="#FFB300"), line=dict(color="#FFB300",dash="dot")))
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
            yaxis=dict(gridcolor="#1E3A5F", title="Avg Churn %"),
            yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.1),
            margin=dict(t=40,b=20,l=10,r=10), title="Churn by Segment")
        st.plotly_chart(fig2, use_container_width=True)

    with cr:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Avg LTV", x=seg_df["SEGMENT"],
            y=seg_df["AVG_LTV"], marker_color="#29B5E8",
            text=["₹"+f"{v:,.0f}" for v in seg_df["AVG_LTV"]],
            textposition="outside"))
        fig3.add_trace(go.Bar(name="LTV at Risk", x=seg_df["SEGMENT"],
            y=seg_df["LTV_AT_RISK"], marker_color="#E63946", opacity=0.7))
        fig3.update_layout(barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E8EDF2", yaxis=dict(gridcolor="#1E3A5F",title="₹ LTV"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=40,b=20,l=10,r=10), title="LTV vs LTV at Risk by Segment")
        st.plotly_chart(fig3, use_container_width=True)

    # Income band analysis
    st.markdown('<p class="section-title">Churn by Income Band</p>',
                unsafe_allow_html=True)
    if not inc_df.empty:
        fig4 = px.scatter(inc_df, x="AVG_CHURN_PCT", y="AVG_LTV",
            size="CUSTOMERS", color="INCOME_BAND",
            color_discrete_sequence=PAL, hover_data=["HIGH_RISK_COUNT"],
            labels={"AVG_CHURN_PCT":"Avg Churn %","AVG_LTV":"Avg LTV (₹)"},
            title="Income Band: Churn vs LTV (bubble = customer count)")
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
            legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig4, use_container_width=True)

# ── Tab 2: Scenario 4 — Claim Severity ────────────────────────
with tab2:
    st.markdown('<p class="section-title">Scenario 4 — Claim Severity by Policy Type</p>',
                unsafe_allow_html=True)
    if not clm_df.empty:
        cl2, cr2 = st.columns(2)
        with cl2:
            fig = go.Figure(go.Bar(
                x=clm_df["POLICY_TYPE"], y=clm_df["AVG_CLAIM_AMOUNT"],
                marker_color="#E63946",
                text=["₹"+f"{v:,.0f}" for v in clm_df["AVG_CLAIM_AMOUNT"]],
                textposition="outside"))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
                yaxis=dict(gridcolor="#1E3A5F", title="Avg Claim Amount (₹)"),
                margin=dict(t=40,b=20,l=10,r=10), title="Avg Claim Amount by Policy Type")
            st.plotly_chart(fig, use_container_width=True)
        with cr2:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Total Claims", x=clm_df["POLICY_TYPE"],
                y=clm_df["TOTAL_CLAIMS"], marker_color="#29B5E8"))
            fig2.add_trace(go.Bar(name="Approved", x=clm_df["POLICY_TYPE"],
                y=clm_df["APPROVED"], marker_color="#2DC653"))
            fig2.update_layout(barmode="group",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E8EDF2", yaxis=dict(gridcolor="#1E3A5F"),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=40,b=20,l=10,r=10), title="Claims Volume & Approvals")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<p class="section-title">Approval Rate by Policy Type</p>',
                    unsafe_allow_html=True)
        for _, r in clm_df.iterrows():
            pct = float(r["APPROVAL_RATE_PCT"] or 0)
            clr = "#2DC653" if pct > 70 else "#FFB300" if pct > 50 else "#E63946"
            st.markdown(f"""
            <div style='background:#0D1B2A;border:1px solid #1E3A5F;
                        border-radius:8px;padding:10px 14px;margin-bottom:6px;
                        display:flex;justify-content:space-between;align-items:center'>
                <b style='color:#F0F4F8'>{r['POLICY_TYPE']}</b>
                <div style='display:flex;gap:20px'>
                    <span style='color:#8FB0CC;font-size:11px'>
                        {int(r['TOTAL_CLAIMS'])} claims · ₹{r['AVG_CLAIM_AMOUNT']:,.0f} avg
                    </span>
                    <span style='color:{clr};font-weight:700'>{pct:.1f}% approved</span>
                </div>
            </div>""", unsafe_allow_html=True)
        st.dataframe(clm_df, use_container_width=True, hide_index=True)

# ── Tab 3: Scenario 8 — Lapses by State ───────────────────────
with tab3:
    st.markdown('<p class="section-title">Scenario 8 — Policy Lapses by State & Segment</p>',
                unsafe_allow_html=True)
    if not lap_df.empty:
        state_agg = lap_df.groupby("STATE")["LAPSED_COUNT"].sum().reset_index()
        state_agg = state_agg.sort_values("LAPSED_COUNT", ascending=False)

        fig = go.Figure(go.Bar(
            x=state_agg["STATE"], y=state_agg["LAPSED_COUNT"],
            marker_color="#E63946",
            text=state_agg["LAPSED_COUNT"], textposition="outside"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
            yaxis=dict(gridcolor="#1E3A5F", title="Lapsed/Cancelled Policies"),
            margin=dict(t=40,b=20,l=10,r=10), title="Policy Lapses by State")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<p class="section-title">Lapses by State + Segment Heatmap</p>',
                    unsafe_allow_html=True)
        pivot = lap_df.pivot_table(index="STATE", columns="SEGMENT",
                                    values="LAPSED_COUNT",
                                    aggfunc="sum").fillna(0)
        fig2 = px.imshow(pivot,
            color_continuous_scale=["#0D2A1A","#FFB300","#E63946"],
            text_auto=True, aspect="auto",
            title="Lapses Heatmap — State × Segment")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
            margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(lap_df.sort_values("LAPSED_COUNT", ascending=False),
                     use_container_width=True, hide_index=True)

# ── Tab 4: Scenario 9 — Channel Effectiveness ─────────────────
with tab4:
    st.markdown('<p class="section-title">Scenario 9 — Channel Effectiveness (Complaint Rate)</p>',
                unsafe_allow_html=True)
    if not ch_df.empty:
        cl3, cr3 = st.columns(2)
        with cl3:
            fig = go.Figure(go.Bar(
                x=ch_df["CHANNEL"], y=ch_df["COMPLAINT_RATE_PCT"],
                marker_color=[
                    "#E63946" if v > 20 else "#FFB300" if v > 10 else "#2DC653"
                    for v in ch_df["COMPLAINT_RATE_PCT"]],
                text=ch_df["COMPLAINT_RATE_PCT"].round(1).astype(str)+"%",
                textposition="outside"))
            fig.add_hline(y=15, line_dash="dot", line_color="#FFB300",
                          annotation_text="15% threshold",
                          annotation_font_color="#FFB300")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
                yaxis=dict(gridcolor="#1E3A5F", title="Complaint Rate %"),
                margin=dict(t=40,b=20,l=10,r=10), title="Complaint Rate by Channel")
            st.plotly_chart(fig, use_container_width=True)
        with cr3:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Total Interactions", x=ch_df["CHANNEL"],
                y=ch_df["TOTAL_INTERACTIONS"], marker_color="#29B5E8"))
            fig2.add_trace(go.Bar(name="Complaints", x=ch_df["CHANNEL"],
                y=ch_df["COMPLAINT_COUNT"], marker_color="#E63946"))
            fig2.update_layout(barmode="overlay",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E8EDF2", yaxis=dict(gridcolor="#1E3A5F"),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=40,b=20,l=10,r=10), title="Interactions vs Complaints")
            st.plotly_chart(fig2, use_container_width=True)

        for _, r in ch_df.iterrows():
            rate = float(r["COMPLAINT_RATE_PCT"] or 0)
            clr  = "#E63946" if rate > 20 else "#FFB300" if rate > 10 else "#2DC653"
            st.markdown(f"""
            <div style='background:#0D1B2A;border:1px solid #1E3A5F;border-radius:8px;
                        padding:10px 14px;margin-bottom:6px;
                        display:flex;justify-content:space-between;align-items:center'>
                <b style='color:#F0F4F8'>{r['CHANNEL']}</b>
                <div style='display:flex;gap:20px'>
                    <span style='color:#8FB0CC;font-size:11px'>
                        {int(r['TOTAL_INTERACTIONS'])} interactions ·
                        {int(r['COMPLAINT_COUNT'])} complaints
                    </span>
                    <span style='color:{clr};font-weight:700'>{rate:.1f}% complaint rate</span>
                </div>
            </div>""", unsafe_allow_html=True)

# ── Tab 5: Sentiment & NBA Distribution ───────────────────────
with tab5:
    st.markdown('<p class="section-title">Call Sentiment Trend</p>',
                unsafe_allow_html=True)
    if not sent_df.empty:
        sent_df["MONTH"] = pd.to_datetime(sent_df["MONTH"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sent_df["MONTH"], y=sent_df["AVG_SENTIMENT"],
            name="Avg Sentiment", mode="lines+markers",
            line=dict(color="#29B5E8", width=2.5),
            fill="tozeroy", fillcolor="rgba(41,181,232,0.08)"))
        fig.add_trace(go.Bar(x=sent_df["MONTH"], y=sent_df["COMPLAINT_CALLS"],
            name="Complaint Calls", marker_color="#E63946", opacity=0.5, yaxis="y2"))
        fig.add_hline(y=0, line_dash="dot", line_color="#8FB0CC",
                      annotation_text="Neutral", annotation_font_color="#8FB0CC")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
            yaxis=dict(gridcolor="#1E3A5F", title="Sentiment Score", range=[-1,1]),
            yaxis2=dict(overlaying="y", side="right", title="Complaint Calls",
                        gridcolor="rgba(0,0,0,0)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.08),
            margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="section-title">NBA Action Distribution</p>',
                unsafe_allow_html=True)
    if not nba_df.empty:
        agg = nba_df.groupby("NBA_PRIORITY")["CUSTOMER_COUNT"].sum().reset_index()
        fig2 = go.Figure(go.Pie(
            labels=agg["NBA_PRIORITY"], values=agg["CUSTOMER_COUNT"],
            hole=0.5,
            marker_colors=["#E63946","#FF6B35","#FFB300","#2DC653"],
            textinfo="label+percent"))
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E8EDF2",
            showlegend=False, height=280, margin=dict(t=20,b=20,l=10,r=10))
        st.plotly_chart(fig2, use_container_width=True)
