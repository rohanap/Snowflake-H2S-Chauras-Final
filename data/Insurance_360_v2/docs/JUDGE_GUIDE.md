# Judge Guide — Insurance 360 (10-minute demo)

**Open:** Snowsight → Projects » Streamlit → **Insurance_360_Final** (`INSURANCE_C360.GOLD.INSURANCE_360_V2`)
Tip: if data looks stale, click **Sync Snowflake** in the sidebar.

| Step | Module | What to do | What you should see | Features shown |
|---|---|---|---|---|
| 1 | **Home** | Scroll the page | KPIs, 7 module cards, Bronze→Silver→Gold→App architecture, 17-feature inventory | Overview |
| 2 | **02 NBA Priority** | Filter to *Urgent*, pick a segment/channel | Ranked action queue with priority, channel, reason, confidence | Snowpark ML, NBA engine |
| 3 | **01 Customer 360** | Search a customer from the queue | Full profile, churn score, NBA, and tabs for policies/claims/payments/interactions/transcripts | Customer 360, AI_AGG |
| 4 | **01 / 02** | Click generate script, then dispatch | Personalised AI outreach text; confirmation of internal + customer email | Cortex COMPLETE, Email Notifications |
| 5 | **03 Segment Analytics** | Switch through the 6 views | Churn/LTV by segment, cross-sell, claim severity, lapse map, channel friction | Gold scenario views |
| 6 | **04 Transcript RAG** | Ask *"Why are customers unhappy with claims?"* | Matching call cards + grounded answer + quality scores | Cortex Search, RAG eval |
| 7 | **05 Ask Your Data** | Ask *"Average churn risk by segment"* (Auto) | Routed to Analyst, SQL shown, chart rendered | Cortex Analyst, Semantic View |
| 8 | **05 Ask Your Data** | Switch to *Cortex Agent*, ask an open question | Multi-tool agent answer | Cortex Agent |
| 9 | **06 Document AI** | Open a policy PDF and an audio call | Extracted policy fields; call transcript | AI_PARSE_DOCUMENT, AI_EXTRACT, AI_TRANSCRIBE |
| 10 | **07 Ops Monitor** | Scroll | Model validation, 24-day NBA trend, distributions, task pipeline | Tasks, Dynamic Tables, ML monitoring |

## Optional: verify it's real data (SQL worksheet)
```sql
SELECT COUNT(*) FROM INSURANCE_C360.GOLD.CHURN_SCORES;          -- 1,000 scored customers
SELECT COUNT(*) FROM INSURANCE_C360.GOLD.URGENT_ALERTS_TODAY;   -- 233 urgent/high alerts
SELECT COUNT(*) FROM INSURANCE_C360.SILVER.ENRICHED_TRANSCRIPTS;-- 866 AI-enriched calls
SHOW TASKS IN DATABASE INSURANCE_C360;                          -- automated pipeline
```

## Judging criteria mapping
| Criterion | Where to look |
|---|---|
| Innovation | 3-engine auto-routed chat (Step 7–8); insight → email in one flow (Step 4) |
| Technical depth | Medallion pipeline, ML scoring, 17 Snowflake features (`HACKATHON_SUBMISSION.md` §3, §5) |
| Business impact | NBA queue & Customer 360 (Steps 2–4) |
| Completeness | Deployed app, automated tasks, full docs set (TRD, App Flow, Plan, Testing) |
| Problem solving | Challenges & solutions (`HACKATHON_SUBMISSION.md` §7) |
