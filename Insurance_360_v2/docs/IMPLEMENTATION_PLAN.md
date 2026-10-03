# Implementation Plan — Insurance 360 v2

## Project Rule
Build one phase at a time. Do not start the next phase until the current phase passes its verification checks.
Phases 0–7 are **complete and deployed**; Phase 8 is the open hardening backlog.

## Phase 0 — Data Foundation ✅
Tasks: load bronze tables in `INSURANCE_C360.MDB_DATA` (customers, policies, claims, payments, interactions, transcripts).
Deliverable: 1,000 customers / 1,642 policies / 866 transcripts available.
Verify: row counts match source.

## Phase 1 — Silver AI Enrichment ✅
Tasks: dynamic tables with SENTIMENT, SUMMARIZE, AI_CLASSIFY, AI_AGG (`ENRICHED_TRANSCRIPTS`, `CUSTOMER_VOC_SIGNALS`);
document AI (`EXTRACTED_POLICY_DOCS`) and audio (`AUDIO_TRANSCRIPTIONS`); Cortex Search `TRANSCRIPT_SEARCH`.
Verify: every transcript has sentiment/summary; search returns results.

## Phase 2 — Gold Analytics + ML ✅
Tasks: `CUSTOMER_360_VIEW`, XGBoost churn model → `CHURN_SCORES`, NBA engine → `NBA_WITH_CONFIDENCE`, scenario views 1–9.
Verify: all 1,000 customers scored; `CHURN_DEPLOYMENT_VALIDATION` populated.

## Phase 3 — Serving Layer ✅
Tasks: semantic view `CUSTOMER_360_SEMANTIC` (10 VQRs), agent `INSURANCE_C360_AGENT`, email integration `C360_EMAIL_NOTIFY`.
Verify: Analyst and Agent answer sample questions.

## Phase 4 — Orchestration ✅
Tasks: nightly task graph (ROOT → SILVER_REFRESH → CHURN_SCORING → NBA_LOG), MORNING_ALERTS, PROCESS_NEW_PDFS.
Verify: `NBA_DAILY_LOG` gains a row per day; `URGENT_ALERTS_TODAY` refreshed.

## Phase 5 — App Shell + Core Pages ✅
Tasks: `snowflake.yml`, container runtime, theme + self-hosted fonts, `utils/data_loader.py`, Home, Customer 360, NBA Priority.
Verify: app deploys; customer lookup and queue work.

## Phase 6 — AI Pages ✅
Tasks: Transcript RAG, Ask Your Data (3-engine router in `utils/rag_agent.py`), Document AI, RAG evaluation.
Verify: each engine returns an answer; SQL displayed.

## Phase 7 — Analytics, Ops, Email ✅
Tasks: Segment Analytics, Ops Monitor, `_email_helpers.dispatch_emails`, `_reload.py` session-safe reload, model upgrade to `mistral-large3`.
Verify: emails delivered; Regenerate works; no Snowpark error 1409.

## Phase 8 — Hardening (open)
Tasks:
- [ ] Use bind parameters in `_send_email` instead of string-built SQL
- [ ] Move internal email recipient to a config table / secret
- [ ] Add a confirmation step before customer email dispatch (if not already enforced)
- [ ] Replace hard-coded Ops task list with live `SHOW TASKS` / `TASK_HISTORY`
- [ ] Set `showErrorDetails = false` before wide sharing
- [ ] Transfer ownership to a least-privilege role instead of `ACCOUNTADMIN`
- [ ] Add automated smoke tests for `utils/` functions
Deliverable: production-ready app for broader business users.
Verify: complete `TESTING.md` checklist, including §10 Security.

## Out of Scope for v2
- Writing back to source policy systems
- Multi-tenant / per-agent row-level security
- External CRM integration (Salesforce etc.)
- Mobile-native app
