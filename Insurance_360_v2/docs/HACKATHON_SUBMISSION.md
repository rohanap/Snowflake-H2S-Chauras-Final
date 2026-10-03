# Insurance 360 — Hackathon Submission

> **An AI-native customer intelligence platform for insurers, built 100% inside Snowflake with Cortex Code.**
> App: `INSURANCE_C360.GOLD.INSURANCE_360_V2` (Streamlit in Snowflake, title "Insurance_360_Final")

---

## 1. The Problem
Insurance retention teams work across disconnected systems — policy admin, claims, billing, call centre
recordings and PDF policy documents. Agents can't see the full customer picture, at-risk customers are
spotted too late, and unstructured data (calls, documents) is effectively unused.

## 2. Our Solution
Insurance 360 unifies **structured + unstructured** data into one 360° view, predicts **who will churn**,
recommends the **Next Best Action**, writes a **personalised outreach message with AI**, and **emails it** —
all in one click, without data ever leaving Snowflake.

## 3. Key Highlights
| | |
|---|---|
| **17 Snowflake features** | Cortex SENTIMENT, SUMMARIZE, COMPLETE, AI_CLASSIFY, AI_AGG, AI_EXTRACT, AI_PARSE_DOCUMENT, AI_TRANSCRIBE, Cortex Search, Cortex Analyst, Cortex Agent, Snowpark ML, Semantic Views, Dynamic Tables, MCP Server, Email Notifications, Web Search |
| **7 app modules** | Customer 360 · NBA Priority · Segment Analytics · Transcript RAG · Ask Your Data · Document AI · Ops Monitor |
| **Full medallion pipeline** | Bronze (6 source tables) → Silver (AI-enriched Dynamic Tables) → Gold (360, ML, NBA) → App |
| **ML in production** | XGBoost churn model scoring **all 1,000 customers**, with train/test baselines and deployment validation |
| **Actionable output** | **1,000** NBA recommendations with confidence; **233** urgent/high alerts snapshotted daily |
| **Automated** | 6-task nightly/stream pipeline; **24 days** of NBA history logged |
| **Measured AI quality** | RAG responses scored live for groundedness / context relevance / answer relevance; agent optimised against a **30-question evaluation set** |
| **Zero data movement** | No external APIs, CDNs or keys — everything runs in the Snowflake security perimeter |

## 4. Data at a Glance
- 1,000 customers · 1,642 policies · 753 claims · 8,016 payments · 2,450 interactions
- 866 call transcripts (sentiment, summary, intent classified)
- 53 policy PDFs parsed and field-extracted · 10 audio calls transcribed

## 5. Architecture
```
 BRONZE  MDB_DATA ─ customers, policies, claims, payments, interactions, transcripts
    │
 SILVER  Dynamic Tables + Cortex AI
    │     SENTIMENT · SUMMARIZE · AI_CLASSIFY · AI_AGG   → ENRICHED_TRANSCRIPTS, CUSTOMER_VOC_SIGNALS
    │     AI_PARSE_DOCUMENT · AI_EXTRACT                 → EXTRACTED_POLICY_DOCS (stream-triggered)
    │     AI_TRANSCRIBE                                  → AUDIO_TRANSCRIPTIONS
    │     Cortex Search (arctic-embed-m-v1.5)            → TRANSCRIPT_SEARCH
    │
 GOLD    CUSTOMER_360_VIEW · CHURN_SCORES (XGBoost) · NBA_WITH_CONFIDENCE
    │     9 business scenario views · NBA_DAILY_LOG · URGENT_ALERTS_TODAY
    │
 SERVE   Semantic View CUSTOMER_360_SEMANTIC (10 verified queries)
         Cortex Agent INSURANCE_C360_AGENT · Email (C360_EMAIL_NOTIFY)
         Streamlit app — 7 modules, container runtime
```
Nightly orchestration: `TASK_ROOT_NIGHTLY` → `TASK_SILVER_REFRESH` → `TASK_CHURN_SCORING` → `TASK_NBA_LOG`,
plus `TASK_MORNING_ALERTS` and stream-driven `TASK_PROCESS_NEW_PDFS`.

## 6. Business Value
- **Earlier churn intervention** — every customer ranked by risk and lifetime value, every morning.
- **Agent productivity** — one screen replaces 5 systems; outreach script written in seconds.
- **Unlocks unstructured data** — calls and PDFs become searchable, queryable signals.
- **Self-service analytics** — business users ask questions in English; the SQL is shown for transparency.
- **Governed by design** — single platform, single security model, no data copies to third-party AI.

## 7. Challenges We Faced & How We Solved Them
| Challenge | Solution |
|---|---|
| **LLM model deprecation mid-build** — `mistral-large2` moved to legacy and started returning HTTP 400, silently breaking every "Regenerate" button | Diagnosed the failure, centralised the model name in one constant (`CORTEX_MODEL`) and upgraded to `mistral-large3` |
| **No internet in the container runtime** — Google Fonts and CDN assets failed silently, design fell back to system fonts | Self-hosted fonts in `static/` with Streamlit static serving; picked Fira Sans as an offline match and simulated heavy weights with CSS text-stroke |
| **Packages unavailable by default** — Plotly isn't pre-installed in container runtimes | Attached `SNOWFLAKE.SNOWPARK.PYPI_SHARED_REPOSITORY` and pinned a version proven to resolve on the account |
| **Dependency download failures (401)** — `boto3/botocore` (transitive deps) couldn't download from the shared repository | Used `uv` override-dependencies with an impossible marker so the resolver skips them entirely |
| **Snowpark error 1409 "More than one active session"** — hot-reloading edited modules created duplicate sessions | Built a custom reload guard (`utils/_reload.py`) that reloads changed modules but keeps the session owner alive, and passes one session to helpers |
| **Calling Cortex Search / Agent from inside the app** | Used SQL functions `SEARCH_PREVIEW` and `DATA_AGENT_RUN` via Snowpark, with robust JSON parsing of mixed text / SQL / tool-result responses |
| **Choosing the right AI engine per question** | Built an auto-router: transcript-style questions → Cortex Search (RAG), metric questions → Cortex Analyst, otherwise → Cortex Agent; user can override |
| **Trusting AI answers** | Added live LLM-as-judge scoring for RAG, confidence strips per engine, and always display the generated SQL |
| **Theme legibility** — an early CSS-only theme produced white-on-white sidebar buttons | Moved palette into native Streamlit theme config (`[theme.sidebar]`) so colours apply from the first frame |
| **Performance with many AI calls** | Tiered caching (15 min rows, 30 min aggregates, 10 min AI) plus a one-click "Sync Snowflake" refresh |

## 8. What Makes It Innovative
1. **End-to-end in one platform** — ingestion, AI enrichment, ML, semantic layer, agent, app and email.
2. **Three AI engines, one chat box** — Agent, Analyst and Search auto-routed.
3. **From insight to action** — prediction → recommendation → AI message → delivered email.
4. **Unstructured as first-class data** — PDFs and audio processed automatically as they land.
5. **Built entirely with Cortex Code** (AI-assisted, "vibe coded"), documented with TRD / App Flow / Plan / Testing.

## 9. Roadmap
- Parameterised email calls and configurable recipients
- Least-privilege service role and role-based PII masking
- Live task history in Ops Monitor
- CRM write-back (e.g. Salesforce) and campaign effectiveness tracking

## 10. Supporting Documents
- `docs/JUDGE_GUIDE.md` — 10-minute guided demo
- `docs/OBJECTS_AND_FUNCTIONS.md` — every Snowflake object, AI function and task, and what it does
- `docs/TRD.md` · `docs/APP_FLOW.md` · `docs/IMPLEMENTATION_PLAN.md` · `docs/TESTING.md`
