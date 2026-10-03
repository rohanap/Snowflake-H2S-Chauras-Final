# Prompt for generating the hackathon presentation

Copy everything below the line into your PPT tool (Gamma, Copilot in PowerPoint, Beautiful.ai, ChatGPT, etc.).
For best results, also attach `HACKATHON_SUBMISSION.md`, `JUDGE_GUIDE.md` and `OBJECTS_AND_FUNCTIONS.md`.

---

You are an expert pitch-deck designer for technical hackathons. Create a **14-slide, 16:9 presentation**
for my hackathon submission **"Insurance 360 — AI-Native Customer Intelligence for Insurers"**, built
entirely on Snowflake using Cortex Code (AI-assisted development).

**Audience:** hackathon judges (technical and business). **Tone:** confident, clear, results-focused.
**Rules:** max 5 bullets per slide, max 12 words per bullet; use icons, diagrams and large numbers instead of
paragraphs. Add short speaker notes (60–90 words) to every slide. Use only the facts below; do not invent
metrics such as accuracy, revenue or ROI.

**Visual style:** Bauhaus / neo-brutalist, matching the app. Warm off-white background `#f5f0e8`, near-black
ink `#1a1a1a`, accent yellow `#ffcc00`, red `#e63b2e`, blue `#0055ff`. Square corners, thick black 2px
borders, bold geometric headings (Fira Sans or similar), monospace labels (JetBrains Mono) for tech names.
Leave placeholder frames labelled "[Screenshot: …]" where app screenshots should go.

### Slide plan

1. **Title:** "Insurance 360". Subtitle: "From customer signals to retention action — 100% inside Snowflake". Team name placeholder, hackathon name placeholder.

2. **The Problem:** Insurer data is siloed (policy, claims, billing, call centre, PDFs). Agents lack a full customer view. Churn is spotted too late. Calls and documents go unused.

3. **Our Solution:** One app that unifies structured and unstructured data → predicts churn → recommends the Next Best Action → writes AI outreach → sends the email. Show as a 5-step horizontal flow.

4. **By the Numbers:** big-number tiles: **17** Snowflake features · **7** app modules · **1,000** customers scored · **866** calls AI-enriched · **53** PDFs + **10** audio calls processed · **233** urgent alerts daily · **6** automated tasks · **0** data leaving Snowflake.

5. **Architecture:** layered diagram:
   - Bronze `MDB_DATA`: 6 source tables (1,000 customers, 1,642 policies, 753 claims, 8,016 payments, 2,450 interactions, 866 transcripts)
   - Silver: Dynamic Tables with SENTIMENT, SUMMARIZE, AI_CLASSIFY, AI_AGG; AI_PARSE_DOCUMENT + AI_EXTRACT; AI_TRANSCRIBE; Cortex Search
   - Gold: Customer 360 view, XGBoost churn scores, NBA engine, 9 business scenario views
   - Serving: Semantic View (10 verified queries), Cortex Agent, Email notifications, Streamlit app (container runtime)

6. **Cortex AI at Work:** a grid of AI functions, each with a one-line job:
   SENTIMENT (score every call) · SUMMARIZE (call summaries) · AI_CLASSIFY (intent: complaint, cancellation risk, upsell…) · COMPLETE / mistral-large3 (topics, resolution, outreach scripts) · AI_AGG (recurring themes per customer) · AI_PARSE_DOCUMENT + AI_EXTRACT (11 fields from policy PDFs) · AI_TRANSCRIBE (audio to text) · Cortex Search (semantic RAG) · Cortex Analyst (text-to-SQL) · Cortex Agent (orchestration).

7. **Module 1–2: Customer 360 + NBA Priority:** full profile across 5 ledgers; churn score; Next Best Action with channel, priority and confidence; one-click AI script and email dispatch. [Screenshot: Customer 360] [Screenshot: NBA queue]

8. **Module 3–4: Segment Analytics + Transcript RAG:** 6 views (segment risk, cross-sell, claim severity, lapse geography, channel friction, voice & actions); semantic search over 866 calls with grounded answers and live quality scores (groundedness, context relevance, answer relevance). [Screenshots]

9. **Module 5: Ask Your Data:** one chat box, three engines auto-routed: transcript questions → Cortex Search, metric questions → Cortex Analyst, open questions → Cortex Agent. Generated SQL is always shown; auto charts. [Screenshot]

10. **Module 6–7: Document AI + Ops Monitor:** PDFs auto-processed as they land (stream-triggered task); audio transcription; model validation, 24-day NBA trend, pipeline health. [Screenshots]

11. **Fully Automated Pipeline:** timeline diagram: TASK_ROOT_NIGHTLY (20:30 UTC) → SILVER_REFRESH → CHURN_SCORING → NBA_LOG; TASK_MORNING_ALERTS (00:30 UTC) builds today's urgent list; TASK_PROCESS_NEW_PDFS runs hourly when new files arrive.

12. **Challenges We Overcame:** 2-column "Challenge → Solution" table, 5 rows:
    - LLM deprecated mid-build (mistral-large2 returned errors) → centralised model config, upgraded to mistral-large3
    - No internet in the app runtime (fonts/CDN failed) → self-hosted fonts and static assets
    - Packages missing / 401 download errors → shared PyPI artifact repository + uv dependency overrides
    - Snowpark "more than one active session" error → custom session-safe module reload guard
    - Choosing the right AI engine → built a keyword router across Agent / Analyst / Search, with user override

13. **Business Impact & Innovation:** earlier churn intervention with a daily risk-ranked queue; one screen replaces five systems; unstructured data becomes queryable; self-service analytics with transparent SQL; governed — no data copied to external AI. Innovation: insight → action → delivery in a single click.

14. **Roadmap & Thank You:** next: parameterised email calls and configurable recipients, least-privilege role with PII masking, live task history, CRM write-back and campaign tracking. Closing line: "Built entirely with Snowflake Cortex Code." Q&A.

Output the deck with consistent layouts, a title on every slide, and slide numbers.
