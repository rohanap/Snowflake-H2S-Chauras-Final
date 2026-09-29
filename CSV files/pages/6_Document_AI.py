"""
Page 6 -- Document AI & Audio Intelligence
PDF extraction via AI_PARSE_DOCUMENT + AI_EXTRACT
Audio transcription via AI_TRANSCRIBE
"""
import streamlit as st
import json
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.theme import apply_theme
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Document AI", page_icon="📄", layout="wide")
apply_theme()
session = get_active_session()

# ── Hero ──
st.html(
    '<div class="bh-hero"><h1>Document & Audio Intelligence</h1>'
    '<p>AI-powered extraction from policy PDFs (AI_PARSE_DOCUMENT + AI_EXTRACT) '
    'and call recording transcription (AI_TRANSCRIBE + SENTIMENT + AI_CLASSIFY)</p></div>'
)

# ── KPI Tiles ──
stats = session.sql("""
    SELECT COUNT(*) AS total_docs,
        COUNT(DISTINCT EXTRACTED_FIELDS:response:policy_type::VARCHAR) AS policy_types,
        ROUND(AVG(EXTRACTED_FIELDS:response:premium::FLOAT), 2) AS avg_premium,
        ROUND(AVG(EXTRACTED_FIELDS:response:deductible::FLOAT), 2) AS avg_deductible
    FROM INSURANCE_C360.SILVER.EXTRACTED_POLICY_DOCS
""").to_pandas()
audio_stats = session.sql("""
    SELECT COUNT(*) AS audio_files, ROUND(AVG(SENTIMENT_SCORE), 4) AS avg_sent
    FROM INSURANCE_C360.SILVER.AUDIO_TRANSCRIPTIONS
""").to_pandas()

r = stats.iloc[0]
a = audio_stats.iloc[0]
st.html(f"""
<div class="bh-grid">
    <div class="bh-tile"><div class="bh-tile-label">PDFs Processed</div>
        <div class="bh-tile-value">{int(r['TOTAL_DOCS'])}</div>
        <div class="bh-tile-sub">AI_PARSE_DOCUMENT + AI_EXTRACT</div></div>
    <div class="bh-tile t-warn"><div class="bh-tile-label">Policy Types</div>
        <div class="bh-tile-value">{int(r['POLICY_TYPES'])}</div>
        <div class="bh-tile-sub">Distinct types extracted</div></div>
    <div class="bh-tile"><div class="bh-tile-label">Avg Premium</div>
        <div class="bh-tile-value">INR {r['AVG_PREMIUM']:,.0f}</div>
        <div class="bh-tile-sub">Across all policies</div></div>
    <div class="bh-tile t-accent"><div class="bh-tile-label">Audio Transcribed</div>
        <div class="bh-tile-value">{int(a['AUDIO_FILES'])}</div>
        <div class="bh-tile-sub">AI_TRANSCRIBE / Avg Sent: {a['AVG_SENT']:.2f}</div></div>
</div>
""")

# ── Tabs for PDF vs Audio ──
tab_pdf, tab_audio = st.tabs(["PDF Documents", "Audio Transcriptions"])

# ╔══════════════════════════════════════╗
# ║ TAB 1: PDF DOCUMENTS                 ║
# ╚══════════════════════════════════════╝
with tab_pdf:
    st.html('<div class="bh-section-title">Extracted Policy Documents</div>')

    col_f1, col_f2 = st.columns(2)
    types_df = session.sql("""
        SELECT DISTINCT EXTRACTED_FIELDS:response:policy_type::VARCHAR AS POLICY_TYPE
        FROM INSURANCE_C360.SILVER.EXTRACTED_POLICY_DOCS
        WHERE EXTRACTED_FIELDS:response:policy_type IS NOT NULL ORDER BY 1
    """).to_pandas()

    with col_f1:
        selected_type = st.selectbox("Filter by Policy Type", ["All"] + types_df["POLICY_TYPE"].tolist())
    with col_f2:
        search_term = st.text_input("Search document content", placeholder="e.g. flood damage, hospitalization")

    where_clauses = []
    if selected_type != "All":
        where_clauses.append(f"EXTRACTED_FIELDS:response:policy_type::VARCHAR = '{selected_type}'")
    if search_term:
        where_clauses.append(f"PARSED_TEXT ILIKE '%{search_term}%'")
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    docs_df = session.sql(f"""
        SELECT EXTRACTED_FIELDS:response:policy_number::VARCHAR AS "Policy Number",
            EXTRACTED_FIELDS:response:policy_type::VARCHAR AS "Type",
            EXTRACTED_FIELDS:response:customer_name::VARCHAR AS "Customer",
            EXTRACTED_FIELDS:response:customer_id::VARCHAR AS "Customer ID",
            EXTRACTED_FIELDS:response:premium::FLOAT AS "Premium (INR)",
            EXTRACTED_FIELDS:response:sum_insured::FLOAT AS "Sum Insured (INR)",
            EXTRACTED_FIELDS:response:deductible::FLOAT AS "Deductible (INR)",
            EXTRACTED_FIELDS:response:start_date::VARCHAR AS "Start Date",
            EXTRACTED_FIELDS:response:end_date::VARCHAR AS "End Date",
            FILE_NAME AS "Source File"
        FROM INSURANCE_C360.SILVER.EXTRACTED_POLICY_DOCS WHERE {where_sql} ORDER BY 1
    """).to_pandas()

    st.dataframe(docs_df, use_container_width=True, height=380)

    # Detail viewer
    st.html('<div class="bh-section-title">Document Detail</div>')
    if not docs_df.empty:
        selected_policy = st.selectbox("Select a policy", docs_df["Policy Number"].tolist())
        if selected_policy:
            detail = session.sql(f"""
                SELECT EXTRACTED_FIELDS:response:benefits::VARCHAR AS BENEFITS,
                    EXTRACTED_FIELDS:response:exclusions::VARCHAR AS EXCLUSIONS,
                    LEFT(PARSED_TEXT, 2000) AS FULL_TEXT
                FROM INSURANCE_C360.SILVER.EXTRACTED_POLICY_DOCS
                WHERE EXTRACTED_FIELDS:response:policy_number::VARCHAR = '{selected_policy}'
            """).to_pandas()

            if not detail.empty:
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    benefits_html = ""
                    try:
                        items = json.loads(detail["BENEFITS"].iloc[0])
                        benefits_html = "".join(f"<span class='bh-pill bh-p-low'>{b}</span>" for b in items)
                    except Exception:
                        benefits_html = str(detail["BENEFITS"].iloc[0] or "")
                    st.html(f'<div class="bh-card"><div class="bh-card-title">Coverage & Benefits</div>{benefits_html}</div>')

                with col_d2:
                    excl_html = ""
                    try:
                        items = json.loads(detail["EXCLUSIONS"].iloc[0])
                        excl_html = "".join(f"<span class='bh-pill bh-p-urgent'>{e}</span>" for e in items)
                    except Exception:
                        excl_html = str(detail["EXCLUSIONS"].iloc[0] or "")
                    st.html(f'<div class="bh-card"><div class="bh-card-title">Exclusions</div>{excl_html}</div>')

                with st.expander("View Full Parsed Document"):
                    st.text(detail["FULL_TEXT"].iloc[0])
    else:
        st.info("No documents match the current filters.")

    # Analytics
    st.html('<div class="bh-section-title">Document Analytics</div>')
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        type_dist = session.sql("""
            SELECT EXTRACTED_FIELDS:response:policy_type::VARCHAR AS POLICY_TYPE, COUNT(*) AS DOC_COUNT
            FROM INSURANCE_C360.SILVER.EXTRACTED_POLICY_DOCS GROUP BY 1 ORDER BY 2 DESC
        """).to_pandas()
        st.bar_chart(type_dist.set_index("POLICY_TYPE"), color="#1a1a1a")
    with col_c2:
        premium_by_type = session.sql("""
            SELECT EXTRACTED_FIELDS:response:policy_type::VARCHAR AS POLICY_TYPE,
                ROUND(AVG(EXTRACTED_FIELDS:response:premium::FLOAT), 2) AS AVG_PREMIUM,
                ROUND(AVG(EXTRACTED_FIELDS:response:deductible::FLOAT), 2) AS AVG_DEDUCTIBLE
            FROM INSURANCE_C360.SILVER.EXTRACTED_POLICY_DOCS GROUP BY 1 ORDER BY 2 DESC
        """).to_pandas()
        st.bar_chart(premium_by_type.set_index("POLICY_TYPE")[["AVG_PREMIUM", "AVG_DEDUCTIBLE"]])

# ╔══════════════════════════════════════╗
# ║ TAB 2: AUDIO TRANSCRIPTIONS          ║
# ╚══════════════════════════════════════╝
with tab_audio:
    st.html('<div class="bh-section-title">Audio Call Transcriptions</div>')
    st.html("""
    <div class="bh-card">
        <div class="bh-card-title">Pipeline Flow</div>
        <div style="font-family:monospace;font-size:0.85rem;line-height:1.8">
            <b>MP3 Audio</b> &rarr; AI_TRANSCRIBE (Speech-to-Text)
            &rarr; CORTEX.SENTIMENT &rarr; CORTEX.SUMMARIZE &rarr; AI_CLASSIFY (Intent)
        </div>
    </div>
    """)

    audio_df = session.sql("""
        SELECT FILE_NAME, CALL_ID, CUSTOMER_ID,
            LEFT(TRANSCRIBED_TEXT, 200) AS TRANSCRIPT_PREVIEW,
            SENTIMENT_SCORE, CUSTOMER_INTENT,
            LEFT(CALL_SUMMARY, 200) AS SUMMARY
        FROM INSURANCE_C360.SILVER.AUDIO_TRANSCRIPTIONS
        ORDER BY FILE_NAME
    """).to_pandas()

    if not audio_df.empty:
        st.dataframe(audio_df, use_container_width=True, hide_index=True)

        st.html('<div class="bh-section-title">Transcription Detail</div>')
        selected_call = st.selectbox("Select a call", audio_df["CALL_ID"].tolist())
        if selected_call:
            call_detail = session.sql(f"""
                SELECT TRANSCRIBED_TEXT, SENTIMENT_SCORE, CALL_SUMMARY, CUSTOMER_INTENT, FILE_NAME
                FROM INSURANCE_C360.SILVER.AUDIO_TRANSCRIPTIONS
                WHERE CALL_ID = '{selected_call}'
            """).to_pandas()
            if not call_detail.empty:
                cd = call_detail.iloc[0]
                sent = float(cd['SENTIMENT_SCORE'])
                sent_class = "bh-g-good" if sent > 0.3 else "bh-g-warn" if sent > 0 else "bh-g-bad"
                pct = min(100, max(5, int((sent + 1) / 2 * 100)))

                st.html(f"""
                <div class="bh-card">
                    <div class="bh-card-title">Call Analysis</div>
                    <div class="bh-kv"><span class="bh-kv-k">Audio File</span><span class="bh-kv-v">{cd['FILE_NAME']}</span></div>
                    <div class="bh-kv"><span class="bh-kv-k">Intent</span><span class="bh-kv-v"><span class="bh-pill bh-p-info">{cd['CUSTOMER_INTENT']}</span></span></div>
                    <div class="bh-gauge-wrap">
                        <div class="bh-gauge-top"><span>Sentiment</span><span>{sent:.4f}</span></div>
                        <div class="bh-gauge-track"><div class="bh-gauge-fill {sent_class}" style="width:{pct}%"></div></div>
                    </div>
                </div>
                """)

                st.html(f'<div class="bh-card"><div class="bh-card-title">AI Summary</div><p>{cd["CALL_SUMMARY"]}</p></div>')

                with st.expander("Full Transcription"):
                    st.text(cd["TRANSCRIBED_TEXT"])
    else:
        st.info("No audio transcriptions available.")

st.caption("Powered by Snowflake AI_PARSE_DOCUMENT, AI_EXTRACT, and AI_TRANSCRIBE")
