# Snowflake Objects & Functions Reference — Insurance 360

Every object and AI function the solution uses, and what it does. Database: `INSURANCE_C360`.

## 1. Cortex AI Functions

| Function | Where used | What it does |
|---|---|---|
| `SNOWFLAKE.CORTEX.SENTIMENT` | `SILVER.ENRICHED_TRANSCRIPTS` | Scores each call transcript from -1 (negative) to +1 (positive) |
| `SNOWFLAKE.CORTEX.SUMMARIZE` | `SILVER.ENRICHED_TRANSCRIPTS` | Writes a short summary of every call |
| `AI_CLASSIFY` | `SILVER.ENRICHED_TRANSCRIPTS` | Labels customer intent: complaint, cancellation_risk, claim_inquiry, renewal_inquiry, upsell_interest, general_query |
| `SNOWFLAKE.CORTEX.COMPLETE` (`mistral-large3`) | Transcripts DT; app pages 01, 02, 04, 05 | Extracts key topics and a resolved yes/no/partial flag per call; writes personalised NBA outreach scripts; writes grounded RAG answers; scores RAG quality (LLM-as-judge) |
| `AI_AGG` | `SILVER.CUSTOMER_VOC_SIGNALS` | Combines all of a customer's call summaries into their 2–3 recurring themes |
| `AI_PARSE_DOCUMENT` (LAYOUT mode) | `TASK_PROCESS_NEW_PDFS` | Reads text and layout from policy PDFs on a stage |
| `AI_EXTRACT` | `TASK_PROCESS_NEW_PDFS` | Pulls 11 structured fields from each policy: number, type, holder, premium, sum insured, deductible, dates, benefits, exclusions |
| `AI_TRANSCRIBE` | `SILVER.AUDIO_TRANSCRIPTIONS` | Converts recorded call audio to text |
| `SNOWFLAKE.CORTEX.SEARCH_PREVIEW` | `utils/rag_agent.py` (pages 04, 05) | Runs semantic search over the transcript search service from inside the app |
| `SNOWFLAKE.CORTEX.DATA_AGENT_RUN` | `utils/rag_agent.py` (page 05) | Calls the Cortex Agent and Cortex Analyst (text-to-SQL) from inside the app |

## 2. Data Objects by Layer

### Bronze — `MDB_DATA` (raw source)
| Object | Rows | Purpose |
|---|---|---|
| `INSURANCE_CUSTOMER` | 1,000 | Customer master: name, segment, city/state, income, contact |
| `POLICY` | 1,642 | Policies, premiums, status, dates |
| `CLAIM` | 753 | Claims and their amounts and status |
| `PAYMENT` | 8,016 | Premium payments, including failed ones |
| `INTERACTION` | 2,450 | Contact history: channel, agent, subject |
| `CALL_TRANSCRIPT` | 866 | Raw call-centre transcripts |

### Silver — `SILVER` (AI-enriched)
| Object | Type | Purpose |
|---|---|---|
| `ENRICHED_TRANSCRIPTS` | Dynamic Table (1 h lag) | Each call with sentiment, summary, intent, key topics, resolution flag and estimated duration |
| `CUSTOMER_VOC_SIGNALS` | Dynamic Table (1 h lag) | Voice of the customer per person: call counts, average/min sentiment, last call, AI_AGG recurring themes, complaint and cancellation-risk counts |
| `EXTRACTED_POLICY_DOCS` | Table (53) | Parsed text plus extracted fields from policy PDFs |
| `AUDIO_TRANSCRIPTIONS` | Table (10) | Transcribed audio calls |
| `ALL_TRANSCRIPTS_UNIFIED` | View | Text and audio transcripts in one place |
| `DIM_CUSTOMERS` | View | Clean customer dimension |
| `FACT_POLICY_SIGNALS` / `FACT_CLAIM_SIGNALS` / `FACT_PAYMENT_SIGNALS` / `FACT_INTERACTION_SIGNALS` | Views | Per-customer feature signals used by the churn model and the 360 view |
| `POLICY_DOCUMENT_SIGNALS` | View | Document-derived features per policy |
| `POLICY_DOCS_STREAM` | Stream | Detects new PDFs arriving on stage `STAGE_DATA.POLICY_DOCS` |
| `TRANSCRIPT_SEARCH` | Cortex Search Service | Semantic (vector + keyword) index over transcripts, using `snowflake-arctic-embed-m-v1.5` embeddings |

### Gold — `GOLD` (analytics, ML, serving)
| Object | Type | Purpose |
|---|---|---|
| `CUSTOMER_360_BASE` / `CUSTOMER_360_VIEW` | Views | One row per customer joining all signals, churn score and NBA; the app's main data source |
| `CHURN_SCORES` | Table (1,000) | Churn probability and risk label from the XGBoost model |
| `CHURN_TRAIN_BASELINE` / `CHURN_TEST_BASELINE` | Tables (750 / 250) | Training and test splits used for the model |
| `CHURN_GROUND_TRUTH` / `CHURN_SCORES_LABELED` | Tables | Actual outcomes, for checking the model |
| `CHURN_DEPLOYMENT_VALIDATION` | Table | Results of the post-deployment model check (Ops Monitor) |
| `CHURN_MONITOR_VIEW` | View | Ongoing model monitoring |
| `NBA_WITH_CONFIDENCE` | View | Next Best Action, its channel, priority, reason and confidence |
| `SCENARIO_1_HIGH_VALUE_AT_RISK` | View | High-LTV customers likely to churn |
| `SCENARIO_2_CROSS_SELL` | View | Cross-sell opportunities |
| `SCENARIO_3_PAYMENT_RISK` | View | Customers with failed or late payments |
| `SCENARIO_4_CLAIM_SEVERITY` | View | Claim severity analysis |
| `SCENARIO_5_SERVICE_RECOVERY` | View | Unhappy customers who need service recovery |
| `SCENARIO_8_LAPSES_BY_STATE` | View | Policy lapses by geography |
| `SCENARIO_9_CHANNEL_EFFECTIVENESS` | View | Which contact channels work best |
| `NBA_DAILY_LOG` | Table (24 days) | Daily snapshot of NBA counts by priority, average churn and LTV at risk |
| `URGENT_ALERTS_TODAY` | Table (233) | Today's Urgent/High customers for morning outreach |
| `REFRESH_CHURN_SCORES()` | Stored Procedure | Re-scores every customer; called by the nightly task |
| `CUSTOMER_360_SEMANTIC` | Semantic View | Business definitions of metrics and dimensions, with 10 verified queries, used by Cortex Analyst |
| `INSURANCE_C360_AGENT` | Cortex Agent | Answers questions by orchestrating Analyst (structured data) and Search (transcripts) |
| `EVAL_DATASET_INSURANCE_C360_AGENT_OPT_*` | Table (30) | Evaluation questions used to optimise the agent |
| `INSURANCE_360_V2` | Streamlit App | The 7-module user interface |

## 3. Automation — Tasks (warehouse `C360_WH`)

| Task | Schedule | What it does |
|---|---|---|
| `GOLD.TASK_ROOT_NIGHTLY` | CRON 20:30 UTC daily | Starts the nightly task graph |
| `GOLD.TASK_SILVER_REFRESH` | After ROOT | Refreshes `ENRICHED_TRANSCRIPTS` and `CUSTOMER_VOC_SIGNALS` |
| `GOLD.TASK_CHURN_SCORING` | After SILVER_REFRESH | `CALL REFRESH_CHURN_SCORES()`: re-scores all customers |
| `GOLD.TASK_NBA_LOG` | After CHURN_SCORING | Appends today's NBA and churn summary to `NBA_DAILY_LOG` |
| `GOLD.TASK_MORNING_ALERTS` | CRON 00:30 UTC daily | Rebuilds `URGENT_ALERTS_TODAY` from Urgent/High customers |
| `SILVER.TASK_PROCESS_NEW_PDFS` | Every 60 min, only when `POLICY_DOCS_STREAM` has data | Parses and extracts new PDFs into `EXTRACTED_POLICY_DOCS` |

```
TASK_ROOT_NIGHTLY → TASK_SILVER_REFRESH → TASK_CHURN_SCORING → TASK_NBA_LOG
TASK_MORNING_ALERTS (independent)      TASK_PROCESS_NEW_PDFS (stream-triggered)
```

## 4. Integrations & Platform

| Object | What it does |
|---|---|
| `C360_EMAIL_NOTIFY` (notification integration) | Lets `SYSTEM$SEND_EMAIL` send the internal NBA dispatch email and the customer outreach email |
| `STAGE_DATA.POLICY_DOCS` (stage) | Stores the policy PDF files |
| `SNOWFLAKE.SNOWPARK.PYPI_SHARED_REPOSITORY` | Supplies Python packages (Plotly) to the app's container runtime |
| `SYSTEM_COMPUTE_POOL_CPU` | Compute pool that runs the Streamlit container |
| `COMPUTE_WH` / `C360_WH` | Warehouses for app queries / pipeline and tasks |

## 5. App Code Modules

| File | What it does |
|---|---|
| `streamlit_app.py` | Home page: KPIs, module navigation, architecture, feature inventory |
| `pages/1_Customer_360.py` | 360° profile, ledgers, AI outreach script |
| `pages/2_NBA_Dashboard.py` | Prioritised NBA queue, live script, email dispatch |
| `pages/3_Segment_Analytics.py` | 6 analytic views built on the scenario views |
| `pages/4_Transcript_Explorer.py` | Cortex Search RAG over transcripts |
| `pages/5_Ask_Your_Data.py` | Chat over three engines with SQL and charts |
| `pages/6_Document_AI.py` | Policy PDF and audio transcription browser |
| `pages/7_Ops_Monitor.py` | Model validation, NBA trends, pipeline status |
| `pages/_email_helpers.py` | Builds the HTML emails and calls `SYSTEM$SEND_EMAIL` |
| `utils/data_loader.py` | Snowpark session, parameterised cached queries, NBA message generation |
| `utils/rag_agent.py` | Cortex Search, Analyst and Agent calls, the question router, RAG evaluation |
| `utils/_reload.py` | Reloads edited modules safely, keeping one Snowpark session |
| `utils/theme.py` + `.streamlit/config.toml` | Bauhaus visual theme, self-hosted fonts |
