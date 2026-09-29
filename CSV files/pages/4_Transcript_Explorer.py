"""
Page 4 — Transcript Explorer (RAG)
Cortex Search over INSURANCE_C360.SILVER.ENRICHED_TRANSCRIPTS.
Returns ranked results + AI synthesis. Follow-up Q&A on results.
"""
import streamlit as st
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.rag_agent import search_transcripts, evaluate_rag_response
from utils.theme import apply_theme
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Transcript Explorer", page_icon="🔍", layout="wide")
apply_theme()
session = get_active_session()

st.markdown("# 🔍 Transcript Explorer")
st.caption(
    "Search insurance call transcripts in plain English via **Cortex Search**. "
    "AI synthesises an answer from the top matching calls."
)

col_q, col_k = st.columns([4,1])
with col_q:
    query = st.text_input("🔍 Search transcripts",
        placeholder="e.g. customers upset about claim delays · policy cancellations · renewal inquiries",
        label_visibility="collapsed")
with col_k:
    top_k = st.selectbox("Results", [3,5,8,10], index=1)

examples = [
    "customers who mentioned cancelling their policy",
    "calls about delayed or rejected claims",
    "customers asking about renewal or premium increase",
    "complaints about poor service or long wait times",
    "customers interested in adding new coverage",
]
st.caption("**Try:** " + "  ·  ".join([f"`{e}`" for e in examples[:3]]))

with st.expander("⚙️ Advanced filters"):
    cust_filter = st.text_input("Filter by Customer ID (optional)",
                                placeholder="e.g. CUST0001")
    eval_mode   = st.checkbox(
        "Show RAG quality scores (Groundedness · Context Relevance · Answer Relevance)")

if not query.strip():
    st.info("Enter a search query to explore call transcripts.")
    st.stop()

with st.spinner("Cortex Search retrieving transcripts…"):
    cf = cust_filter.strip() if cust_filter and cust_filter.strip() else None
    try:
        resp = search_transcripts(query, limit=top_k, customer_filter=cf)
    except Exception as e:
        st.error(f"Cortex Search error: {e}")
        st.info("Ensure TRANSCRIPT_SEARCH service is active: "
                "SHOW CORTEX SEARCH SERVICES IN SCHEMA SILVER;")
        st.stop()

results    = resp.get("results", [])
rag_answer = resp.get("rag_answer", "")

# ── RAG Answer ────────────────────────────────────────────────
if rag_answer:
    st.markdown('<p class="section-title">🤖 AI Answer (Cortex RAG)</p>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div class='ai-box'>
        <p style='color:#29B5E8;font-size:10px;font-weight:700;
                  letter-spacing:2px;margin:0 0 8px 0'>
            CORTEX SEARCH + COMPLETE · RAG SYNTHESIS
        </p>
        <p style='color:#E8EDF2;font-size:13px;line-height:1.8;margin:0'>
            {rag_answer}
        </p>
    </div>""", unsafe_allow_html=True)

    if eval_mode and results:
        with st.spinner("Evaluating RAG quality…"):
            scores = evaluate_rag_response(query, rag_answer, results)
        st.markdown('<p class="section-title" style="margin-top:12px">'
                    'RAG Quality Scores</p>', unsafe_allow_html=True)
        e1,e2,e3 = st.columns(3)
        for col, label, val in [
            (e1, "Groundedness",      scores["groundedness"]),
            (e2, "Context Relevance", scores["context_relevance"]),
            (e3, "Answer Relevance",  scores["answer_relevance"]),
        ]:
            ok = val >= 0.75
            col.metric(label, f"{val:.2f}/1.0",
                       delta="✅ Good" if ok else "⚠️ Review",
                       delta_color="normal" if ok else "inverse")

st.divider()

# ── Result cards ──────────────────────────────────────────────
if not results:
    st.warning("No matching transcripts found. Try a different query.")
else:
    st.markdown(f'<p class="section-title">{len(results)} Matching Transcripts</p>',
                unsafe_allow_html=True)
    for i, r in enumerate(results):
        sent  = float(r.get("SENTIMENT_SCORE", 0))
        s_clr = "#E63946" if sent<-0.3 else "#FFB300" if sent<0.1 else "#2DC653"
        intent = str(r.get("CUSTOMER_INTENT","unknown")).replace("_"," ").title()
        name   = r.get("CUSTOMER_NAME","Unknown")
        date   = str(r.get("INTERACTION_DATE",""))[:10]
        subj   = r.get("SUBJECT","")
        summ   = r.get("CALL_SUMMARY","")
        topics = r.get("KEY_TOPICS","")
        cid    = r.get("CUSTOMER_ID","")
        seg    = r.get("SEGMENT","")
        chan   = r.get("CHANNEL","")

        st.markdown(f"""
        <div class='rag-card'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                <div>
                    <b style='color:#F0F4F8;font-size:13px'>{name}</b>
                    <span style='color:#8FB0CC;font-size:10px;margin-left:8px'>
                        {cid} · {seg}
                    </span>
                </div>
                <span style='color:{s_clr};font-weight:700;font-size:13px'>
                    {round(sent,2)} sentiment
                </span>
            </div>
            <div style='margin:6px 0'>
                <span style='background:#1E3A5F;color:#29B5E8;padding:2px 8px;
                             border-radius:10px;font-size:10px'>{intent}</span>
                <span style='color:#8FB0CC;font-size:10px;margin-left:8px'>
                    📅 {date} · 📞 {chan}
                </span>
            </div>
            <p style='color:#FFB300;font-size:11px;margin:4px 0'>
                <b>Subject:</b> {subj}
            </p>
            <p style='color:#E8EDF2;font-size:12px;margin:4px 0;line-height:1.6'>
                {summ}
            </p>
            <p style='color:#8FB0CC;font-size:10px;margin:0'>
                <b>Topics:</b> {topics}
            </p>
        </div>""", unsafe_allow_html=True)

        with st.expander(f"📄 Full transcript — {name} ({date})"):
            c1,c2 = st.columns([3,1])
            with c1:
                st.text_area("", r.get("TRANSCRIPT_TEXT",""), height=200,
                             key=f"txt_{i}", label_visibility="collapsed")
            with c2:
                st.metric("Sentiment", round(sent,3))
                st.metric("Intent",    intent)
                st.metric("Channel",   chan)
                if st.button("→ View 360", key=f"nav_{i}"):
                    st.info(f"Go to Customer 360 page and search for: {cid}")

st.divider()

# ── Follow-up Q&A ─────────────────────────────────────────────
if results:
    st.markdown('<p class="section-title">💬 Follow-up on These Results</p>',
                unsafe_allow_html=True)
    st.caption("Ask a follow-up — answered using only the transcripts retrieved above.")
    followup = st.text_input("Your question:", key="followup",
        placeholder="e.g. What resolution did these customers receive?")
    if followup and st.button("Ask", type="primary"):
        context = "\n\n---\n\n".join([
            f"Customer: {r.get('CUSTOMER_NAME')}\n"
            f"Subject: {r.get('SUBJECT','')}\n"
            f"Summary: {r.get('CALL_SUMMARY','')}"
            for r in results
        ])
        prompt = (
            "Answer using ONLY the call summaries below. "
            "Be specific. If the answer is not in the summaries, say so.\n\n"
            f"SUMMARIES:\n{context}\n\nQUESTION: {followup}"
        ).replace("'","''")
        with st.spinner("Cortex COMPLETE thinking…"):
            ans = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2','{prompt}') AS A
            """).to_pandas()["A"].iloc[0]
        st.markdown(f"""
        <div class='ai-box'>
            <p style='color:#E8EDF2;line-height:1.7;margin:0'>{ans}</p>
        </div>""", unsafe_allow_html=True)
