"""
Page 5 — Ask Your Data
Auto-routes questions to Cortex Analyst (metrics) or
Cortex Search (transcripts) for INSURANCE_C360.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.rag_agent import ask_agent
from utils.theme import apply_theme
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Ask Your Data", page_icon="💬", layout="wide")
apply_theme()
session = get_active_session()

st.markdown("# 💬 Ask Your Data")
st.caption(
    "One input, three engines. **Metrics** → Cortex Analyst (Text-to-SQL). "
    "**Calls & transcripts** → Cortex Search (RAG). "
    "**Cortex Agent** → Orchestrates both tools automatically via the INSURANCE_C360_AGENT object."
)

with st.expander("⚙️ How routing works"):
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""
**📊 → Cortex Analyst (Text-to-SQL)**
- *How many high-risk customers are there?*
- *Average LTV by segment?*
- *Which state has the most lapses?*
- *Total premium at risk from churn?*
- *NBA priority breakdown by income band?*
""")
    with c2:
        st.markdown("""
**🔍 → Cortex Search (RAG)**
- *Customers who mentioned cancelling*
- *Calls about delayed claims*
- *Complaints about premium increases*
- *Customers upset with service quality*
- *Renewal inquiries from high-LTV customers*
""")

st.divider()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

col_q, col_m = st.columns([4,1])
with col_m:
    force = st.selectbox("Mode",["Auto","Cortex Agent","Cortex Analyst","Cortex Search"])
    mode_map = {"Auto":None,"Cortex Agent":"agent","Cortex Analyst":"analyst","Cortex Search":"search"}

# Example questions
st.markdown('<p class="section-title">Example Questions</p>', unsafe_allow_html=True)
tab_a, tab_s = st.tabs(["📊 Analyst","🔍 Search"])
analyst_qs = [
    "How many high risk customers are there?",
    "What is the average lifetime value by segment?",
    "Which state has the highest average churn risk?",
    "Total LTV at risk from high churn customers?",
    "How many customers are in each NBA priority?",
    "Average sentiment score by income band?",
]
search_qs = [
    "customers who want to cancel their policy",
    "calls about rejected or delayed insurance claims",
    "customers asking about premium or renewal",
    "complaints about service quality or wait times",
    "customers interested in adding life cover",
]
with tab_a:
    cols = st.columns(3)
    for i, q in enumerate(analyst_qs):
        if cols[i%3].button(q, key=f"aq_{i}", use_container_width=True):
            st.session_state["prefill"] = q
with tab_s:
    cols = st.columns(3)
    for i, q in enumerate(search_qs):
        if cols[i%3].button(q, key=f"sq_{i}", use_container_width=True):
            st.session_state["prefill"] = q

prefill  = st.session_state.pop("prefill","")
question = st.chat_input("Ask anything about your policyholders…") or prefill

# Show history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["text"])
        else:
            mode_lbl = ("CORTEX AGENT — Orchestrated"
                        if msg.get("mode")=="agent"
                        else "CORTEX ANALYST — Text-to-SQL"
                        if msg.get("mode")=="analyst"
                        else "CORTEX SEARCH — RAG")
            mode_clr = "#A855F7" if msg.get("mode")=="agent" else "#29B5E8" if msg.get("mode")=="analyst" else "#FFB300"
            st.markdown(f"""
            <div style='background:#0A1E35;border-left:3px solid {mode_clr};
                        padding:6px 12px;border-radius:4px;margin-bottom:8px'>
                <span style='color:{mode_clr};font-size:10px;font-weight:700'>
                    ⚙ {mode_lbl}
                </span>
                <span style='color:#8FB0CC;font-size:10px;margin-left:10px'>
                    Confidence: {msg.get("confidence",0):.0%}
                </span>
            </div>""", unsafe_allow_html=True)
            if msg.get("answer"):
                st.markdown(msg["answer"])
            if msg.get("sql"):
                with st.expander("🔍 Generated SQL"):
                    st.code(msg["sql"], language="sql")
            if msg.get("data") is not None and not msg["data"].empty:
                st.dataframe(msg["data"], use_container_width=True, hide_index=True)
            if msg.get("chart"):
                st.plotly_chart(msg["chart"], use_container_width=True)
            if msg.get("results"):
                for r in msg["results"][:3]:
                    st.markdown(f"""
                    <div class='rag-card'>
                        <b style='color:#F0F4F8'>{r.get("CUSTOMER_NAME","")}</b>
                        <span style='color:#8FB0CC;font-size:10px;margin-left:8px'>
                            {str(r.get("INTERACTION_DATE",""))[:10]}
                        </span><br>
                        <p style='color:#E8EDF2;font-size:12px;margin:4px 0 0 0'>
                            {r.get("CALL_SUMMARY","")}
                        </p>
                    </div>""", unsafe_allow_html=True)

# Process new question
if question and question.strip():
    st.session_state.chat_history.append({"role":"user","text":question})
    with st.chat_message("user"):
        st.markdown(question)

    forced = mode_map[force]
    with st.chat_message("assistant"):
        with st.spinner("Agent thinking…"):
            resp = ask_agent(question,
                             history=st.session_state.chat_history[:-1],
                             force_mode=forced)

        mode       = resp["mode"]
        answer     = resp.get("answer","")
        sql_text   = resp.get("sql","")
        results    = resp.get("results",[])
        confidence = resp.get("confidence",0)
        chart_hint = resp.get("chart_hint","bar")
        error      = resp.get("error")

        mode_lbl = ("CORTEX AGENT — Orchestrated"
                    if mode=="agent"
                    else "CORTEX ANALYST — Text-to-SQL"
                    if mode=="analyst" else "CORTEX SEARCH — RAG")
        mode_clr = "#A855F7" if mode=="agent" else "#29B5E8" if mode=="analyst" else "#FFB300"

        st.markdown(f"""
        <div style='background:#0A1E35;border-left:3px solid {mode_clr};
                    padding:6px 12px;border-radius:4px;margin-bottom:10px'>
            <span style='color:{mode_clr};font-size:10px;font-weight:700'>
                ⚙ {mode_lbl}
            </span>
            <span style='color:#8FB0CC;font-size:10px;margin-left:10px'>
                Confidence: {confidence:.0%}
            </span>
        </div>""", unsafe_allow_html=True)

        if confidence < 0.5:
            st.warning("⚠️ Low confidence — try rephrasing or switching mode.")

        if error:
            st.error(f"Agent error: {error}")
            st.info("Ensure Cortex Search Service and Semantic View are active.")

        result_df = pd.DataFrame()
        fig       = None

        if mode == "agent":
            st.markdown(f"""
            <div class='ai-box'>
                <p style='color:#A855F7;font-size:10px;font-weight:700;
                          letter-spacing:2px;margin:0 0 8px 0'>CORTEX AGENT RESPONSE</p>
                <p style='color:#E8EDF2;line-height:1.7;margin:0'>{answer}</p>
            </div>""", unsafe_allow_html=True)
            if sql_text:
                with st.expander("Generated SQL (from Agent)"):
                    st.code(sql_text, language="sql")
                try:
                    result_df = session.sql(sql_text).to_pandas()
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                except Exception:
                    pass
        elif mode == "analyst":
            if answer:
                st.markdown(answer)
            if sql_text:
                with st.expander("🔍 Generated SQL"):
                    st.code(sql_text, language="sql")
                try:
                    result_df = session.sql(sql_text).to_pandas()
                    st.dataframe(result_df, use_container_width=True, hide_index=True)

                    num_cols = result_df.select_dtypes(include="number").columns.tolist()
                    cat_cols = result_df.select_dtypes(exclude="number").columns.tolist()

                    if len(result_df) > 1 and num_cols and cat_cols:
                        x_col = cat_cols[0]
                        y_col = num_cols[0]

                        if chart_hint == "line" and len(result_df) > 2:
                            fig = px.line(result_df, x=x_col, y=y_col,
                                          markers=True,
                                          color_discrete_sequence=["#29B5E8"])
                        elif chart_hint == "pie" and len(result_df) <= 8:
                            fig = px.pie(result_df, names=x_col, values=y_col,
                                         hole=0.5,
                                         color_discrete_sequence=px.colors.qualitative.Set2)
                        else:
                            fig = px.bar(result_df, x=x_col, y=y_col,
                                         color_discrete_sequence=["#29B5E8"],
                                         text_auto=".3s")
                        if fig:
                            fig.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#E8EDF2",
                                margin=dict(t=30,b=20,l=10,r=10),
                                yaxis=dict(gridcolor="#1E3A5F"),
                                xaxis=dict(gridcolor="#1E3A5F"),
                                showlegend=(chart_hint=="pie"))
                            st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"SQL execution error: {e}")
        else:
            if answer:
                st.markdown(f"""
                <div class='ai-box'>
                    <p style='color:#FFB300;font-size:10px;font-weight:700;
                              letter-spacing:2px;margin:0 0 8px 0'>RAG SYNTHESIS</p>
                    <p style='color:#E8EDF2;line-height:1.7;margin:0'>{answer}</p>
                </div>""", unsafe_allow_html=True)
            if results:
                st.markdown(f"**{len(results)} matching transcripts:**")
                for r in results[:4]:
                    sent  = float(r.get("SENTIMENT_SCORE",0))
                    s_clr = "#E63946" if sent<-0.3 else "#FFB300" if sent<0.1 else "#2DC653"
                    st.markdown(f"""
                    <div class='rag-card'>
                        <div style='display:flex;justify-content:space-between'>
                            <b style='color:#F0F4F8'>{r.get("CUSTOMER_NAME","")}</b>
                            <span style='color:{s_clr};font-weight:700'>
                                {round(sent,2)} sentiment
                            </span>
                        </div>
                        <span style='color:#8FB0CC;font-size:10px'>
                            {str(r.get("INTERACTION_DATE",""))[:10]} ·
                            {r.get("CHANNEL","")} ·
                            {str(r.get("CUSTOMER_INTENT","")).replace("_"," ").title()}
                        </span>
                        <p style='color:#FFB300;font-size:11px;margin:4px 0'>
                            {r.get("SUBJECT","")}
                        </p>
                        <p style='color:#E8EDF2;font-size:12px;margin:0;line-height:1.6'>
                            {r.get("CALL_SUMMARY","")}
                        </p>
                    </div>""", unsafe_allow_html=True)
            elif not answer:
                st.info("No matching transcripts found. Try a different phrasing.")

        st.session_state.chat_history.append({
            "role":"assistant","mode":mode,"text":answer,
            "answer":answer,"sql":sql_text,"results":results,
            "data":result_df,"chart":fig,"confidence":confidence,
        })

if st.session_state.chat_history:
    st.divider()
    if st.button("🗑️ Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()
