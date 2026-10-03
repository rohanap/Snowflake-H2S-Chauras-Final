# Testing Guide — Insurance 360 v2

## 1. Testing Goal
Confirm the deployed app (`INSURANCE_C360.GOLD.INSURANCE_360_V2`) loads every module, shows correct data,
handles AI failures safely, and only sends emails when a user explicitly dispatches them.

## 2. Critical User Journey
```
Open app → 02 NBA Priority → select Urgent customer → 01 Customer 360
→ Generate script → Dispatch email → confirmation shown
```
Do not release if this journey is broken.

## 3. App Load / Navigation
[ ] Home shows KPIs, 7 module cards, architecture, feature inventory
[ ] Every page link opens without an exception
[ ] Sync Snowflake clears caches and data reloads
[ ] Fonts render (self-hosted), theme applied from first paint

## 4. Data Correctness (run in a SQL worksheet and compare to UI)
[ ] Customer count = 1,000 (`MDB_DATA.INSURANCE_CUSTOMER`)
[ ] Policy count = 1,642, transcripts = 866
[ ] A sample customer's policies/claims/payments match the source tables
[ ] Churn score in UI matches `GOLD.CHURN_SCORES` for that customer
[ ] NBA queue priority order: Urgent → High → Medium → Low

## 5. Customer 360
[ ] Search by ID and by name works
[ ] No-match search shows a friendly empty state
[ ] All 5 ledgers render; empty ledgers don't break layout
[ ] Generate script returns text (model `mistral-large3`)
[ ] Regenerate works; AI failure shows error without losing profile

## 6. NBA Priority + Email
[ ] Filters (segment, channel) and sort update the queue
[ ] Pagination (25/page) works at last page
[ ] Dispatch sends internal email via `C360_EMAIL_NOTIFY`
[ ] Customer email sent only when EMAIL exists; otherwise "(no customer email on file)"
[ ] Double-click does not send duplicate emails
[ ] Names containing apostrophes / special characters send correctly

## 7. AI Engines
[ ] Transcript RAG returns cards + grounded answer + RAG scores
[ ] Nonsense query returns low-confidence, not an exception
[ ] Ask Your Data — Auto routes "how many…by segment" to Analyst
[ ] Auto routes "what did customers complain about" to Search
[ ] Cortex Agent mode returns an answer
[ ] Generated SQL is displayed and the result/chart matches it
[ ] Engine error is shown in chat and user can retry

## 8. Document AI / Segment Analytics / Ops
[ ] Policy documents list (53) filters by type and term; detail opens
[ ] Audio list (10) and call detail open
[ ] All 6 Segment Analytics views render charts
[ ] Ops Monitor: model validation, NBA daily log, distributions render
[ ] Task statuses match `SHOW TASKS IN DATABASE INSURANCE_C360`

## 9. Responsive / Accessibility
[ ] Laptop, large monitor, tablet widths: no horizontal overflow
[ ] Widgets have labels; keyboard can reach controls; focus visible
[ ] Priority/status not conveyed by colour alone

## 10. Security / Privacy
[ ] No credentials or tokens in source files
[ ] User text goes into SQL only via bind parameters (check `_send_email`)
[ ] Only intended roles have USAGE on the Streamlit app
[ ] Error details are not exposed to business users (`showErrorDetails`)
[ ] Customer PII (email, phone) only visible to authorised roles

## 11. Release Blockers
- Any module throws an unhandled exception
- Emails sent without explicit user action, or to the wrong recipient
- Churn/NBA values disagree with Gold tables
- Ask Your Data runs SQL that differs from what is displayed
- PII visible to unauthorised roles

## 12. Test Result Format
- Test:
- Expected:
- Actual:
- Page / browser:
- Steps to reproduce:
- Screenshot / query ID:
- Severity:
- Status:
