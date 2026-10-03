# App Flow — Insurance 360 v2

## 1. Entry Points
- Snowsight → Projects » Streamlit → `INSURANCE_360_V2` ("Insurance_360_Final")
- Direct app URL (shared with a role that has USAGE on the app)
- Sidebar page links (any module can be opened directly)

## 2. Primary Journey — Retention outreach
```
Home (KPIs + module cards)
→ 02 NBA Priority (queue sorted Urgent → Low)
→ Filter by segment / channel
→ Select a customer row
→ 01 Customer 360 (profile, churn score, NBA, ledgers)
→ Generate AI outreach script (Cortex COMPLETE)
→ Review / regenerate script
→ Dispatch email (internal team + customer)
→ Success message showing recipients
```

## 3. Screen Details

### Home
Purpose: overview and navigation.
Content: headline KPIs, 7 module cards, pipeline architecture (Bronze → Silver → Gold → App), feature inventory.
Actions: open any module; sidebar **Sync Snowflake** clears caches and re-reads data.

### 01 Customer 360
Inputs: customer search (ID/name).
Shows: profile, churn score, NBA action/channel/priority/confidence, AI_AGG signals, tabs for
Policies / Claims / Payments / Interactions / Transcripts.
Actions: generate or regenerate outreach script.
Empty state: no customer selected → prompt to search. Ledger with no rows → empty ledger.
Errors: AI failure → message shown, profile stays visible.

### 02 NBA Priority
Shows: queue (25 per page) with priority, segment, channel, reason.
Actions: filter, sort, page; generate live agent script; dispatch emails.
Decision point: customer has no email → only the internal email is sent and UI reports "(no customer email on file)".

### 03 Segment Analytics
Actions: switch view — Segment Risk, Cross-Sell, Claim Severity, Lapse Geography, Channel Friction, Voice & Actions.
States: loading spinner, chart per view.

### 04 Transcript RAG
Inputs: free-text question or example prompt.
System: Cortex Search retrieves top transcripts → COMPLETE writes a grounded answer → RAG scores shown.
Empty result: low-confidence message, no cards.

### 05 Ask Your Data
Inputs: question; engine selector (Auto / Cortex Agent / Cortex Analyst / Cortex Search); tabs Metrics // Analyst and Transcripts // Search.
Decision point (Auto): transcript keywords → Search; metric keywords → Analyst; otherwise default routing.
System: shows engine + confidence strip, answer, generated SQL, result table and chart.
Errors: engine error text shown in chat; user can retry or switch engine.

### 06 Document AI
Views: Policy Documents (filter by policy type / term, open detail) and Audio Transcriptions (list → call detail).
Actions: clear filters. Pagination 12 per page.

### 07 Ops Monitor
Shows: churn model validation, NBA daily log trend, churn & confidence distributions, task pipeline table, alert status.
Read-only.

## 4. Secondary Flows
- **Analyst exploration:** Home → 05 Ask Your Data → ask metric question → view SQL → chart.
- **Voice of customer:** Home → 04 Transcript RAG → search complaint theme → open transcript cards.
- **Data refresh:** any page → sidebar Sync Snowflake → page reloads with fresh data.
- **Ops check:** Home → 07 Ops Monitor → verify nightly tasks and model health.

## 5. Important States
- Loading (spinner / loading block)
- Empty (no customer selected, no search results, no ledger rows)
- AI generation error (Cortex COMPLETE / Agent / Analyst failure)
- Search with no results (low confidence)
- Email sent / partial send (no customer email)
- Cached vs refreshed data (after Sync Snowflake)
