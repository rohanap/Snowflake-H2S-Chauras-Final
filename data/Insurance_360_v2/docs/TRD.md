# Technical Requirements Document — Insurance 360 v2

> Status: **Deployed** (as-built documentation). Keep this file current when a technical decision changes.

## 1. Project Overview
Insurance 360 v2 is a Streamlit-in-Snowflake app for insurance customer-success, retention and
analytics teams. It combines a policyholder 360° profile, an ML churn score, a Next-Best-Action (NBA)
engine and Cortex AI features (search, text-to-SQL, agent, document/audio AI) in one 7-module UI, and
can dispatch AI-written outreach emails.

| Item | Value |
|---|---|
| Streamlit object | `INSURANCE_C360.GOLD.INSURANCE_360_V2` |
| Title | `Insurance_360_Final` |
| Workspace source | `Insurance_360_v2/` (main file `streamlit_app.py`) |
| Owner role / execute as | `ACCOUNTADMIN` / `OWNER` |
| Query warehouse | `COMPUTE_WH` |
| Runtime | Container runtime (`run_mode: SpcsOnly`) on `SYSTEM_COMPUTE_POOL_CPU` |
| Package repository | `SNOWFLAKE.SNOWPARK.PYPI_SHARED_REPOSITORY` |

## 2. Technical Goals
- One place to see a customer's policies, claims, payments, interactions, transcripts, churn risk and NBA.
- Prioritised, filterable NBA execution queue across all 1,000 policyholders.
- Natural-language access to data (Cortex Agent / Analyst / Search) with visible generated SQL.
- All data and AI processing stays inside Snowflake (no outbound network from the runtime).
- Responsive page loads through Streamlit caching (15–30 min TTL) with a manual "Sync Snowflake" refresh.

## 3. Tech Stack
- **Frontend/App:** Streamlit `>=1.54.0` (multipage: `streamlit_app.py` + `pages/1..7`), Plotly `5.18.0`, `python-dateutil`
- **Language:** Python `>=3.11`, dependency lock via `uv.lock`
- **Data access:** Snowpark session (`utils/data_loader.get_session()`), parameterised SQL (`_q(sql, params)`)
- **Database:** Snowflake `INSURANCE_C360` — medallion layout `MDB_DATA` (bronze) → `SILVER` → `GOLD`
- **AI:** `SNOWFLAKE.CORTEX.COMPLETE` (`mistral-large3`), `SNOWFLAKE.CORTEX.SEARCH_PREVIEW`,
  `SNOWFLAKE.CORTEX.DATA_AGENT_RUN`, AI_PARSE_DOCUMENT / AI_EXTRACT / AI_TRANSCRIBE (pipeline side), AI_AGG
- **ML:** XGBoost churn model (Snowpark ML), scores in `GOLD.CHURN_SCORES`
- **Notifications:** `SYSTEM$SEND_EMAIL` via notification integration `C360_EMAIL_NOTIFY`
- **Orchestration:** Snowflake Tasks + Dynamic Tables (see §6)
- **Styling:** Bauhaus / neo-brutalist theme (`.streamlit/config.toml` + `utils/theme.py`), self-hosted fonts in `static/`
- **Auth:** Snowflake/Snowsight authentication; app runs with owner's rights. No in-app login.

## 4. Functional Requirements

### Home (`streamlit_app.py`)
- Show headline KPIs, links to the 7 modules, pipeline architecture and feature inventory.
- Sidebar "Sync Snowflake" button clears all caches (`clear_all_caches`).

### 01 Customer 360 (`pages/1_Customer_360.py`)
- Search/select a customer; show profile, churn score, NBA and confidence.
- Ledgers: Policies, Claims, Payments, Interactions, Transcripts.
- Generate / regenerate an AI outreach script (Cortex COMPLETE, `mistral-large3`); show AI_AGG signals.

### 02 NBA Priority (`pages/2_NBA_Dashboard.py`)
- Queue of NBA actions ordered by priority (Urgent → High → Medium → Low), 25 rows per page.
- Filter by segment and channel; sort options.
- Generate a live agent script and dispatch outreach emails (internal + customer) via `_email_helpers.dispatch_emails`.

### 03 Segment Analytics (`pages/3_Segment_Analytics.py`)
- Views: Segment Risk, Cross-Sell, Claim Severity, Lapse Geography, Channel Friction, Voice & Actions (Plotly).

### 04 Transcript RAG (`pages/4_Transcript_Explorer.py`)
- Semantic search over 866 call transcripts via Cortex Search service `INSURANCE_C360.SILVER.TRANSCRIPT_SEARCH`
  (embedding `snowflake-arctic-embed-m-v1.5`), with grounded AI synthesis and RAG quality scoring
  (groundedness, context relevance, answer relevance).

### 05 Ask Your Data (`pages/5_Ask_Your_Data.py`)
- Chat with modes Auto / Cortex Agent / Cortex Analyst / Cortex Search.
- Auto mode routes by keywords (`utils/rag_agent._route`): transcript words → Search, metric words → Analyst.
- Analyst uses semantic view `INSURANCE_C360.GOLD.CUSTOMER_360_SEMANTIC`; agent is `INSURANCE_C360.GOLD.INSURANCE_C360_AGENT`.
- Show generated SQL, run it, chart the result (line/bar/pie hint), show confidence.

### 06 Document AI (`pages/6_Document_AI.py`)
- Browse 53 extracted policy PDFs (`SILVER.EXTRACTED_POLICY_DOCS`) with filters and detail view.
- Browse 10 audio transcriptions (`SILVER.AUDIO_TRANSCRIPTIONS`), 12 items per page.

### 07 Ops Monitor (`pages/7_Ops_Monitor.py`)
- Model validation (`GOLD.CHURN_DEPLOYMENT_VALIDATION`), NBA daily trend (`GOLD.NBA_DAILY_LOG`),
  churn and confidence distributions, task pipeline and alert status.

## 5. Non-Functional Requirements
- **Performance:** row-level reads cached 900 s, aggregates 1,800 s, AI/search results 600 s.
- **Feedback:** every load shows a loading state; AI/agent failures return an error string, never crash the page.
- **Security:** SQL uses bind parameters (`?`) for user input; no secrets in source; runtime has no outbound internet.
- **Resilience:** `utils/_reload.py` reloads edited modules so a single Snowpark session is reused (avoids error 1409).
- **Accessibility/visual:** high-contrast palette, visible borders, labelled widgets.

## 6. Data & Integrations

| Layer | Objects (key) |
|---|---|
| Bronze `MDB_DATA` | `INSURANCE_CUSTOMER` (1,000), `POLICY` (1,642), `CLAIM` (753), `PAYMENT` (8,016), `INTERACTION` (2,450), `CALL_TRANSCRIPT` (866) |
| Silver | `ENRICHED_TRANSCRIPTS` (866), `CUSTOMER_VOC_SIGNALS` (628), `EXTRACTED_POLICY_DOCS` (53), `AUDIO_TRANSCRIPTIONS` (10), `DIM_CUSTOMERS`, `FACT_*_SIGNALS` views, Cortex Search `TRANSCRIPT_SEARCH` |
| Gold | `CUSTOMER_360_VIEW`, `CUSTOMER_360_BASE`, `CHURN_SCORES`, `NBA_WITH_CONFIDENCE`, `NBA_DAILY_LOG`, `SCENARIO_1..9_*` views, `URGENT_ALERTS_TODAY`, `CHURN_DEPLOYMENT_VALIDATION`, semantic view `CUSTOMER_360_SEMANTIC`, agent `INSURANCE_C360_AGENT` |

Scheduled pipeline (as listed in Ops Monitor):

| Task | Schedule | Purpose |
|---|---|---|
| `TASK_ROOT_NIGHTLY` | CRON 20:30 UTC daily | Root of nightly pipeline |
| `TASK_SILVER_REFRESH` | After ROOT | Refresh Silver dynamic tables |
| `TASK_CHURN_SCORING` | After SILVER | Re-score all customers |
| `TASK_NBA_LOG` | After SCORING | Append daily NBA summary |
| `TASK_MORNING_ALERTS` | CRON 00:30 UTC | Snapshot Urgent/High NBA |
| `TASK_PROCESS_NEW_PDFS` | 60 min (stream) | AI_PARSE + AI_EXTRACT new PDFs |

Email: `SYSTEM$SEND_EMAIL('C360_EMAIL_NOTIFY', ...)` — one internal email (full details) + one customer email (script only, skipped if no email on file).

## 7. Constraints
- Must run on the container runtime with the shared PyPI artifact repository (Plotly is not pre-installed).
- No external CDNs — fonts and assets must be self-hosted in `static/` (`enableStaticServing = true`).
- Only one Snowpark session per process; helpers must receive the caller's session.
- `mistral-large2` is deprecated in this account — use `mistral-large3` (`CORTEX_MODEL` in `utils/data_loader.py`).
- `botocore`/`boto3` are excluded via `uv` overrides (they fail to download from the shared repository).
- Customer emails are outward-facing: dispatch must remain an explicit user action.

## 8. Known Technical Risks / Open Items
- `_email_helpers._send_email` builds the `CALL SYSTEM$SEND_EMAIL` statement with string formatting (only `'` escaped); should be switched to bind parameters.
- Internal email recipient is hard-coded in `pages/_email_helpers.py`; move to config/table.
- Task list on Ops Monitor is a hard-coded list, not live `SHOW TASKS` output.
- `[client] showErrorDetails = true` exposes stack traces to viewers; set to `false` for broad sharing.
- App runs as `ACCOUNTADMIN` owner; consider a least-privilege owner role before sharing widely.

## 9. Definition of Done
- All 7 modules load without error on the deployed app.
- Customer 360 → NBA → script → email journey works end to end.
- Ask Your Data returns answers in all three engines.
- No known critical security issues (items in §8 triaged).
- `TESTING.md` release checklist completed.
