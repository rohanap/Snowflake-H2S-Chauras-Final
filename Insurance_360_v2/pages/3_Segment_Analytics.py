"""
Page 3 -- SEGMENT ANALYTICS   (Bauhaus / Neo-Brutalist)
Built from stitch_snowflake_streamlit_ui_redesign/segment_analytics/
  headings: CHURN RISK & LTV BY SEGMENT / LTV AT STAKE (CRORE) /
            INCOME BAND & CHANNEL FRICTION MATRIX

Plotly is restyled to the brutalist palette: flat solid fills, 2px black
marker outlines, no gradients, square corners, hard gridlines. Views sit behind
a segmented control rather than st.tabs, because st.tabs renders hidden bodies
and would fire every query on every rerun.
"""
import os
import sys
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.modules.pop("utils._reload", None)
from utils._reload import refresh_helpers  # noqa: E402

refresh_helpers()

from utils.data_loader import (  # noqa: E402
    clear_all_caches, load_channel_effectiveness, load_claim_severity,
    load_cross_sell, load_high_value_at_risk, load_income_band_analysis,
    load_lapses_by_state, load_nba_distribution, load_segment_analytics,
    load_sentiment_trend,
)
from utils.theme import (  # noqa: E402
    BLUE, BRIGHT, CONTAINER_TOP, INK, MUTED, PAPER, RED, YELLOW, apply_theme,
    banner, bento, inr, kpi, loading, section, sidebar, topbar,
)

st.set_page_config(page_title="Segment Analytics // Insurance Twin",
                   page_icon="⬛", layout="wide")
apply_theme()
sidebar()

banner(
    "Segment Analytics",
    "Cohort-level churn and value analysis &mdash; segment risk, income-band "
    "behaviour, claim severity by product, lapse geography and channel friction. "
    "<b>Scenarios 1, 4, 8 and 9.</b>",
    eyebrow="Cohort Engine // Aggregate Layer",
)

# Brutalist Plotly base: flat fills, black outlines, square everything.
PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=BRIGHT,
    font=dict(family="Inter, system-ui, sans-serif", color=INK, size=12),
    margin=dict(t=44, b=34, l=54, r=18),
    showlegend=False,
    bargap=0.28,
)
AXIS = dict(gridcolor=CONTAINER_TOP, linecolor=INK, linewidth=2,
            zerolinecolor=INK, ticks="outside", tickcolor=INK)
OUTLINE = dict(line=dict(color=INK, width=2))
PALETTE = [INK, YELLOW, RED, BLUE, MUTED, "#a8c6ff"]


def _style(fig, title="", ytitle="", xtitle=""):
    fig.update_layout(
        title=dict(text=title.upper(),
                   font=dict(family="Space Grotesk, sans-serif",
                             size=14, color=INK)),
        **PLOT)
    fig.update_xaxes(title=xtitle.upper(), **AXIS)
    fig.update_yaxes(title=ytitle.upper(), **AXIS)
    return fig


VIEWS = ["Segment Risk", "Cross-Sell", "Claim Severity", "Lapse Geography",
         "Channel Friction", "Voice & Actions"]
view = st.segmented_control("View", VIEWS, default=VIEWS[0], key="s3_view",
                            label_visibility="collapsed") or VIEWS[0]

# ══════════════════════════════════════════════════════════════
if view == VIEWS[0]:
    _t0 = time.perf_counter()
    with loading("Aggregating cohorts"):
        seg = load_segment_analytics()
        risky = load_high_value_at_risk()
    topbar(records=f"{len(seg)} segments", latency=f"{int((time.perf_counter() - _t0) * 1000)} ms")

    if seg.empty:
        st.info("No segment data available.")
        st.stop()

    worst = seg.iloc[0]
    bento([
        kpi("Segments", f"{len(seg)}", "Cohorts scored", icon="◼"),
        kpi("Highest Risk Cohort", str(worst["SEGMENT"]),
            f"{float(worst['AVG_CHURN_RISK_PCT']):.1f}% avg churn",
            tone="red", icon="▲"),
        kpi("Total LTV", inr(seg["TOTAL_LTV"].sum(), compact=True),
            "Book value", tone="dark", icon="₹"),
        kpi("LTV At Stake", inr(seg["LTV_AT_RISK"].sum(), compact=True),
            "High-risk exposure", tone="yellow", icon="◤"),
        kpi("High-Value At Risk", f"{len(risky)}",
            "LTV > ₹5k and churn > 50%", tone="paper", icon="◈"),
    ])

    section("Churn Risk & LTV By Segment", "01")
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Bar(
            x=seg["SEGMENT"], y=seg["AVG_CHURN_RISK_PCT"],
            marker=dict(color=RED, **OUTLINE),
            text=seg["AVG_CHURN_RISK_PCT"].round(1).astype(str) + "%",
            textposition="outside",
            textfont=dict(family="Space Grotesk", size=13, color=INK)))
        st.plotly_chart(_style(fig, "Avg churn by segment", "Churn %"),
                        use_container_width=True)
    with c2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Avg LTV", x=seg["SEGMENT"], y=seg["AVG_LTV"],
                              marker=dict(color=INK, **OUTLINE)))
        fig2.add_trace(go.Bar(name="LTV At Risk", x=seg["SEGMENT"],
                              y=seg["LTV_AT_RISK"],
                              marker=dict(color=YELLOW, **OUTLINE)))
        fig2.update_layout(barmode="group")
        st.plotly_chart(_style(fig2, "LTV vs LTV at stake", "₹"),
                        use_container_width=True)

    section("LTV At Stake", "02")
    mx = float(seg["LTV_AT_RISK"].max()) or 1.0
    bars = "".join(
        f'<div><div class="bh-bar-l"><span>{r["SEGMENT"]}</span>'
        f'<span>{inr(r["LTV_AT_RISK"], compact=True)}</span></div>'
        f'<div class="bh-bar-t"><i style="width:'
        f'{max(2, int(float(r["LTV_AT_RISK"]) / mx * 100))}%;background:{YELLOW}"></i>'
        f'</div></div>'
        for _, r in seg.iterrows())
    st.html('<div class="bh-box"><div class="bh-box-title">'
            '<span>Exposure By Cohort</span><span>High-Risk Only</span></div>'
            f'<div class="bh-bars">{bars}</div></div>')

    section("High-Value Accounts At Risk", "03")
    if risky.empty:
        st.info("No high-value at-risk accounts in the current data.")
    else:
        st.dataframe(
            risky[["NAME", "SEGMENT", "CHURN_RISK_PCT", "LIFETIME_VALUE",
                   "ACTIVE_POLICY_COUNT", "NBA_PRIORITY"]],
            use_container_width=True, hide_index=True, height=420,
            column_config={
                "NAME": st.column_config.TextColumn("Policyholder"),
                "SEGMENT": st.column_config.TextColumn("Segment", width="small"),
                "CHURN_RISK_PCT": st.column_config.ProgressColumn(
                    "Churn", min_value=0, max_value=100, format="%.1f%%"),
                "LIFETIME_VALUE": st.column_config.NumberColumn("LTV", format="₹%.0f"),
                "ACTIVE_POLICY_COUNT": st.column_config.NumberColumn(
                    "Policies", format="%d", width="small"),
                "NBA_PRIORITY": st.column_config.TextColumn("Tier", width="small"),
            })

# ══════════════════════════════════════════════════════════════
elif view == VIEWS[1]:
    _t0 = time.perf_counter()
    with loading("Loading cross-sell candidates"):
        xsell = load_cross_sell()
    topbar(records=f"{len(xsell)} candidates",
           latency=f"{int((time.perf_counter() - _t0) * 1000)} ms")

    if xsell.empty:
        st.info("No cross-sell candidates found.")
        st.stop()

    section("Cross-Sell Opportunities // Scenario 2", "01")

    bento([
        kpi("Candidates", f"{len(xsell)}", "Single-policy, high-LTV", icon="◼"),
        kpi("Total LTV", inr(xsell["LIFETIME_VALUE"].sum(), compact=True),
            "Revenue opportunity", tone="yellow", icon="₹"),
        kpi("Avg Upsell Propensity",
            f"{round(xsell['UPSELL_PROBABILITY'].mean() * 100, 1)}%",
            "Model-scored", tone="paper", icon="◈"),
    ])

    c1, c2 = st.columns(2)
    with c1:
        by_seg = (xsell.groupby("SEGMENT")
                  .agg(COUNT=("CUSTOMER_ID", "count"),
                       LTV=("LIFETIME_VALUE", "sum"))
                  .reset_index().sort_values("LTV", ascending=False))
        fig = go.Figure(go.Bar(
            x=by_seg["SEGMENT"], y=by_seg["LTV"],
            marker=dict(color=YELLOW, **OUTLINE),
            text=[inr(v, compact=True) for v in by_seg["LTV"]],
            textposition="outside",
            textfont=dict(family="Space Grotesk", size=12, color=INK)))
        st.plotly_chart(_style(fig, "Cross-Sell LTV By Segment", "₹"),
                        use_container_width=True)
    with c2:
        by_type = (xsell.groupby("ACTIVE_POLICY_TYPES")["CUSTOMER_ID"]
                   .count().reset_index()
                   .rename(columns={"CUSTOMER_ID": "CT"})
                   .sort_values("CT", ascending=False))
        fig2 = go.Figure(go.Bar(
            x=by_type["ACTIVE_POLICY_TYPES"], y=by_type["CT"],
            marker=dict(color=INK, **OUTLINE),
            text=by_type["CT"], textposition="outside",
            textfont=dict(family="Space Grotesk", size=12, color=INK)))
        st.plotly_chart(_style(fig2, "Current Policy Type (Single)", "Customers"),
                        use_container_width=True)

    section("Candidate Ledger", "02")
    st.dataframe(
        xsell[["NAME", "SEGMENT", "INCOME_BAND", "ACTIVE_POLICY_TYPES",
               "LIFETIME_VALUE", "UPSELL_PROBABILITY", "NBA_ACTION"]],
        use_container_width=True, hide_index=True, height=420,
        column_config={
            "NAME": st.column_config.TextColumn("Policyholder"),
            "SEGMENT": st.column_config.TextColumn("Segment", width="small"),
            "INCOME_BAND": st.column_config.TextColumn("Income", width="small"),
            "ACTIVE_POLICY_TYPES": st.column_config.TextColumn("Current Policy"),
            "LIFETIME_VALUE": st.column_config.NumberColumn("LTV", format="₹%.0f"),
            "UPSELL_PROBABILITY": st.column_config.ProgressColumn(
                "Upsell %", min_value=0, max_value=1, format="%.1f%%"),
            "NBA_ACTION": st.column_config.TextColumn("Action"),
        })

# ══════════════════════════════════════════════════════════════
elif view == VIEWS[2]:
    _t0 = time.perf_counter()
    with loading("Aggregating claim severity"):
        clm = load_claim_severity()
    topbar(records=f"{len(clm)} products", latency=f"{int((time.perf_counter() - _t0) * 1000)} ms")

    if clm.empty:
        st.info("No claim data available.")
        st.stop()

    section("Claim Severity By Policy Type // Scenario 4", "01")
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Bar(
            x=clm["POLICY_TYPE"], y=clm["AVG_CLAIM_AMOUNT"],
            marker=dict(color=RED, **OUTLINE),
            text=[inr(v, compact=True) for v in clm["AVG_CLAIM_AMOUNT"]],
            textposition="outside",
            textfont=dict(family="Space Grotesk", size=12, color=INK)))
        st.plotly_chart(_style(fig, "Avg claim amount", "₹"),
                        use_container_width=True)
    with c2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Total", x=clm["POLICY_TYPE"],
                              y=clm["TOTAL_CLAIMS"],
                              marker=dict(color=INK, **OUTLINE)))
        fig2.add_trace(go.Bar(name="Approved", x=clm["POLICY_TYPE"],
                              y=clm["APPROVED"],
                              marker=dict(color=YELLOW, **OUTLINE)))
        fig2.update_layout(barmode="group")
        st.plotly_chart(_style(fig2, "Volume vs approvals", "Claims"),
                        use_container_width=True)

    section("Approval Rate", "02")
    rows = []
    for _, r in clm.iterrows():
        pct = float(r["APPROVAL_RATE_PCT"] or 0)
        col = YELLOW if pct > 70 else RED if pct < 50 else INK
        rows.append(
            f'<div><div class="bh-bar-l"><span>{r["POLICY_TYPE"]}</span>'
            f'<span>{pct:.1f}% // {int(r["TOTAL_CLAIMS"])} claims</span></div>'
            f'<div class="bh-bar-t"><i style="width:{max(2, int(pct))}%;'
            f'background:{col}"></i></div></div>')
    st.html('<div class="bh-box"><div class="bh-box-title">'
            '<span>Approval Rate By Product</span><span>Approved / Paid</span>'
            f'</div><div class="bh-bars">{"".join(rows)}</div></div>')
    st.dataframe(clm, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
elif view == VIEWS[3]:
    _t0 = time.perf_counter()
    with loading("Aggregating lapse geography"):
        lap = load_lapses_by_state()
    topbar(records=f"{len(lap)} state/segment rows",
           latency=f"{int((time.perf_counter() - _t0) * 1000)} ms")

    if lap.empty:
        st.info("No lapsed or cancelled policies found.")
        st.stop()

    section("Policy Lapses By State // Scenario 8", "01")
    agg = (lap.groupby("STATE")["LAPSED_COUNT"].sum().reset_index()
           .sort_values("LAPSED_COUNT", ascending=False))
    fig = go.Figure(go.Bar(
        x=agg["STATE"], y=agg["LAPSED_COUNT"],
        marker=dict(color=RED, **OUTLINE),
        text=agg["LAPSED_COUNT"], textposition="outside",
        textfont=dict(family="Space Grotesk", size=12, color=INK)))
    st.plotly_chart(_style(fig, "Lapsed / cancelled by state", "Policies"),
                    use_container_width=True)

    section("State × Segment Matrix", "02")
    pivot = lap.pivot_table(index="STATE", columns="SEGMENT",
                            values="LAPSED_COUNT", aggfunc="sum").fillna(0)
    fig2 = px.imshow(pivot, text_auto=True, aspect="auto",
                     color_continuous_scale=[[0, PAPER], [0.5, YELLOW], [1, RED]])
    fig2.update_layout(**{**PLOT, "margin": dict(t=44, b=34, l=90, r=18)})
    fig2.update_layout(title=dict(text="LAPSE DENSITY",
                                  font=dict(family="Space Grotesk", size=14,
                                            color=INK)),
                       coloraxis_colorbar=dict(outlinecolor=INK, outlinewidth=2))
    fig2.update_xaxes(**AXIS)
    fig2.update_yaxes(**AXIS)
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(lap.sort_values("LAPSED_COUNT", ascending=False),
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
elif view == VIEWS[4]:
    _t0 = time.perf_counter()
    with loading("Aggregating channel friction"):
        ch = load_channel_effectiveness()
        inc = load_income_band_analysis()
    topbar(records=f"{len(ch)} channels // {len(inc)} bands",
           latency=f"{int((time.perf_counter() - _t0) * 1000)} ms")

    if ch.empty:
        st.info("No interaction data available.")
        st.stop()

    section("Channel Friction // Scenario 9", "01")
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Bar(
            x=ch["CHANNEL"], y=ch["COMPLAINT_RATE_PCT"],
            marker=dict(
                color=[RED if v > 20 else YELLOW if v > 10 else INK
                       for v in ch["COMPLAINT_RATE_PCT"]], **OUTLINE),
            text=ch["COMPLAINT_RATE_PCT"].round(1).astype(str) + "%",
            textposition="outside",
            textfont=dict(family="Space Grotesk", size=12, color=INK)))
        fig.add_hline(y=15, line_dash="dot", line_color=INK, line_width=2,
                      annotation_text="15% THRESHOLD",
                      annotation_font=dict(family="Space Grotesk", color=INK,
                                           size=11))
        st.plotly_chart(_style(fig, "Complaint rate by channel", "%"),
                        use_container_width=True)
    with c2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Interactions", x=ch["CHANNEL"],
                              y=ch["TOTAL_INTERACTIONS"],
                              marker=dict(color=INK, **OUTLINE)))
        fig2.add_trace(go.Bar(name="Complaints", x=ch["CHANNEL"],
                              y=ch["COMPLAINT_COUNT"],
                              marker=dict(color=RED, **OUTLINE)))
        fig2.update_layout(barmode="overlay")
        st.plotly_chart(_style(fig2, "Volume vs complaints", "Count"),
                        use_container_width=True)

    section("Income Band Behaviour", "02")
    if not inc.empty:
        fig3 = px.scatter(inc, x="AVG_CHURN_PCT", y="AVG_LTV",
                          size="CUSTOMERS", color="INCOME_BAND",
                          color_discrete_sequence=PALETTE,
                          hover_data=["HIGH_RISK_COUNT"])
        fig3.update_traces(marker=dict(line=dict(color=INK, width=2)))
        fig3.update_layout(**{**PLOT, "showlegend": True,
                              "legend": dict(bgcolor=BRIGHT, bordercolor=INK,
                                             borderwidth=2)})
        fig3.update_layout(title=dict(text="CHURN VS LTV BY INCOME BAND",
                                      font=dict(family="Space Grotesk",
                                                size=14, color=INK)))
        fig3.update_xaxes(title="AVG CHURN %", **AXIS)
        fig3.update_yaxes(title="AVG LTV (₹)", **AXIS)
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(inc, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
else:
    _t0 = time.perf_counter()
    with loading("Building voice trend"):
        sent = load_sentiment_trend()
        nba = load_nba_distribution()
    topbar(records=f"{len(sent)} months", latency=f"{int((time.perf_counter() - _t0) * 1000)} ms")

    section("Call Sentiment Trend", "01")
    if sent.empty:
        st.info("No transcript sentiment data available.")
    else:
        s = sent.copy()
        s["MONTH"] = pd.to_datetime(s["MONTH"])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=s["MONTH"], y=s["COMPLAINT_CALLS"],
                             name="Complaints",
                             marker=dict(color=RED, **OUTLINE), yaxis="y2"))
        fig.add_trace(go.Scatter(
            x=s["MONTH"], y=s["AVG_SENTIMENT"], name="Avg Sentiment",
            mode="lines+markers", line=dict(color=INK, width=3),
            marker=dict(size=9, color=YELLOW, line=dict(color=INK, width=2))))
        fig.add_hline(y=0, line_dash="dot", line_color=INK, line_width=2)
        fig.update_layout(**{**PLOT, "showlegend": True,
                             "margin": dict(t=72, b=34, l=54, r=54),
                             "legend": dict(bgcolor=BRIGHT, bordercolor=INK,
                                            borderwidth=2, orientation="h",
                                            yanchor="bottom", y=1.02,
                                            xanchor="right", x=1),
                             "yaxis2": dict(overlaying="y", side="right",
                                            title="COMPLAINTS",
                                            showgrid=False, linecolor=INK,
                                            linewidth=2)})
        fig.update_layout(title=dict(text="SENTIMENT VS COMPLAINT VOLUME",
                                     font=dict(family="Space Grotesk", size=14,
                                               color=INK),
                                     y=0.97, x=0, xanchor="left"))
        fig.update_xaxes(**AXIS)
        fig.update_yaxes(title="SENTIMENT", range=[-1, 1], **AXIS)
        st.plotly_chart(fig, use_container_width=True)

    section("NBA Action Distribution", "02")
    if nba.empty:
        st.info("No NBA distribution available.")
    else:
        agg = (nba.groupby("NBA_PRIORITY")["CUSTOMER_COUNT"].sum()
               .reindex(["Urgent", "High", "Medium", "Low"]).dropna())
        mx = float(agg.max()) or 1.0
        cols = {"Urgent": RED, "High": INK, "Medium": YELLOW, "Low": MUTED}
        bars = "".join(
            f'<div><div class="bh-bar-l"><span>{k}</span><span>{int(v):,}</span></div>'
            f'<div class="bh-bar-t"><i style="width:{max(2, int(v / mx * 100))}%;'
            f'background:{cols.get(k, INK)}"></i></div></div>'
            for k, v in agg.items())
        st.html('<div class="bh-box"><div class="bh-box-title">'
                '<span>Customers By Action Tier</span><span>Count</span></div>'
                f'<div class="bh-bars">{bars}</div></div>')

        top = nba.sort_values("CUSTOMER_COUNT", ascending=False).head(12)
        st.dataframe(top, use_container_width=True, hide_index=True)

with st.sidebar:
    st.button("Sync Snowflake", on_click=clear_all_caches,
              use_container_width=True,
              help="Discard cached results and re-read from Snowflake.")
