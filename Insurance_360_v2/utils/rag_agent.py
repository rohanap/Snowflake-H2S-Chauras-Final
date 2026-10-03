"""
utils/rag_agent.py
Unified agent routing to Cortex Search (transcripts),
Cortex Analyst (Customer 360 metrics), or the Cortex Agent object
for INSURANCE_C360.

Uses SQL functions (SNOWFLAKE.CORTEX.DATA_AGENT_RUN for Agent, and the
Cortex Analyst SQL wrapper via session.sql) so that all calls run through
the Snowpark session. No REST calls or extra SDK imports needed.

Caching note: search_transcripts() runs a Cortex Search call *and* a
CORTEX.COMPLETE synthesis, so an uncached call costs several seconds. It is
memoized on (query, limit, customer_filter) so that ticking a checkbox or
opening an expander no longer replays the whole RAG chain.
"""
import json
import re

import streamlit as st

from utils.data_loader import CORTEX_MODEL, get_session

DB = "INSURANCE_C360"
SCHEMA = "SILVER"
SERVICE = "TRANSCRIPT_SEARCH"
SEM_MDL = f"{DB}.GOLD.CUSTOMER_360_SEMANTIC"
AGENT = f"{DB}.GOLD.INSURANCE_C360_AGENT"

_SEARCH_COLUMNS = [
    "CALL_ID", "CUSTOMER_ID", "CUSTOMER_NAME", "INTERACTION_DATE",
    "CHANNEL", "SUBJECT", "TRANSCRIPT_TEXT", "CALL_SUMMARY",
    "SENTIMENT_SCORE", "CUSTOMER_INTENT", "KEY_TOPICS", "SEGMENT",
]

_TRANSCRIPT_KW = [
    "call", "transcript", "said", "complained", "mentioned", "conversation",
    "spoke", "told", "agent", "discussed", "upset", "cancell", "claim status",
    "unhappy", "resolved", "sentiment", "quote", "customer said",
]
_METRIC_KW = [
    "how many", "count", "average", "total", "sum", "percent", "rate",
    "by segment", "by state", "by income", "by city", "by policy", "compare",
    "trend", "revenue", "premium", "ltv", "lifetime value", "churn risk",
    "highest", "lowest", "most", "least", "distribution", "breakdown",
]


def _route(question: str) -> str:
    return "agent"


def _ensure_warehouse():
    """Make sure the session has an active warehouse for Cortex Agent tools."""
    try:
        get_session().sql("USE WAREHOUSE COMPUTE_WH").collect()
    except Exception:
        pass


def _complete(prompt: str) -> str:
    """Cortex COMPLETE with the prompt bound as a parameter."""
    df = get_session().sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS A",
        params=[CORTEX_MODEL, prompt],
    ).to_pandas()
    return df["A"].iloc[0] if not df.empty else ""


# -- Cortex Search -------------------------------------------------------

_NUMERIC_RESULT_FIELDS = ("SENTIMENT_SCORE",)


def _coerce(record: dict) -> dict:
    """Keep only the requested columns and fix up types."""
    out = {k: record.get(k) for k in _SEARCH_COLUMNS}
    for k in _NUMERIC_RESULT_FIELDS:
        try:
            out[k] = float(out[k]) if out[k] not in (None, "") else 0.0
        except (TypeError, ValueError):
            out[k] = 0.0
    return out


@st.cache_data(ttl=600, max_entries=50, show_spinner=False)
def search_transcripts(query: str, limit: int = 5,
                       customer_filter: str = None) -> dict:
    """Cortex Search over enriched transcripts + RAG synthesis.

    Uses the SNOWFLAKE.CORTEX.SEARCH_PREVIEW SQL function. The request body
    is built with json.dumps and passed as a bound parameter.

    Returns plain dicts so the result is cache-serialisable.
    """
    request = {
        "query": query,
        "columns": _SEARCH_COLUMNS,
        "limit": int(limit),
    }
    if customer_filter:
        request["filter"] = {"@eq": {"CUSTOMER_ID": customer_filter}}

    df = get_session().sql(
        "SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(?, ?)):results::STRING AS R",
        params=[f"{DB}.{SCHEMA}.{SERVICE}", json.dumps(request)],
    ).to_pandas()

    raw = df["R"].iloc[0] if not df.empty else None
    results = [_coerce(r) for r in json.loads(raw)] if raw else []

    if not results:
        return {"results": [], "rag_answer": "No matching transcripts found."}

    context = "\n\n---\n\n".join([
        f"Customer: {r.get('CUSTOMER_NAME', '')}\n"
        f"Date: {str(r.get('INTERACTION_DATE', ''))[:10]}\n"
        f"Subject: {r.get('SUBJECT', '')}\n"
        f"Summary: {r.get('CALL_SUMMARY', '')}"
        for r in results[:3]
    ])
    prompt = (
        "You are an insurance customer insights analyst. "
        "Answer the question using ONLY the call context below. "
        "Be concise and specific. "
        "If the answer is not in the context say so.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION: {query}"
    )
    return {"results": results, "rag_answer": _complete(prompt)}


@st.cache_data(ttl=600, max_entries=50, show_spinner=False)
def answer_from_context(question: str, summaries: tuple) -> str:
    """Follow-up Q&A grounded only in the already-retrieved summaries."""
    context = "\n\n---\n\n".join(summaries)
    prompt = (
        "Answer using ONLY the call summaries below. "
        "Be specific. If the answer is not in the summaries, say so.\n\n"
        f"SUMMARIES:\n{context}\n\nQUESTION: {question}"
    )
    return _complete(prompt)


# -- Cortex Analyst (via SQL) ----------------------------------------------

def query_cortex_analyst(question: str, history: list = None) -> dict:
    messages = []
    if history:
        for h in (history or [])[-4:]:
            role = h.get("role", "") if isinstance(h, dict) else ""
            text = h.get("text", "") if isinstance(h, dict) else ""
            if not text:
                continue
            if role == "assistant":
                role = "analyst"
            if role not in ("user", "analyst"):
                continue
            messages.append({"role": role,
                             "content": [{"type": "text", "text": text}]})
    messages.append({"role": "user",
                     "content": [{"type": "text", "text": question}]})
    try:
        _ensure_warehouse()
        request_body = json.dumps({
            "messages": messages,
            "semantic_view": SEM_MDL,
        })

        df = get_session().sql(
            "SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?)) AS RESP",
            params=[AGENT, request_body],
        ).to_pandas()

        body = json.loads(df["RESP"].iloc[0]) if not df.empty and df["RESP"].iloc[0] else {}

        sql_text = answer_text = ""
        content = body.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "sql":
                        sql_text = item.get("statement", "")
                    elif item.get("type") == "text":
                        answer_text = item.get("text", "")
                    elif item.get("type") == "tool_results":
                        for tc in item.get("content", []):
                            if isinstance(tc, dict) and tc.get("type") == "sql":
                                sql_text = tc.get("statement", "")

        if not sql_text and answer_text:
            sql_match = re.search(r"```sql\s*(.*?)\s*```", answer_text, re.DOTALL)
            if sql_match:
                sql_text = sql_match.group(1).strip()
                answer_text = re.sub(
                    r"```sql\s*.*?\s*```", "", answer_text, flags=re.DOTALL
                ).strip()

        ql = question.lower()
        if any(w in ql for w in ["trend", "over time", "monthly"]):
            chart = "line"
        elif any(w in ql for w in ["by segment", "by state", "by policy", "compare", "breakdown"]):
            chart = "bar"
        elif any(w in ql for w in ["share", "distribution", "proportion", "percent"]):
            chart = "pie"
        else:
            chart = "bar"

        return {"sql": sql_text, "answer": answer_text,
                "chart_hint": chart, "confidence": 0.9 if sql_text else 0.3,
                "error": None}
    except Exception as e:
        return {"sql": "", "answer": "", "chart_hint": "bar",
                "confidence": 0.0, "error": f"{type(e).__name__}: {e}"}


# -- Cortex Agent (via SQL function) --------------------------------------

def query_cortex_agent(question: str) -> dict:
    """Call INSURANCE_C360_AGENT via SNOWFLAKE.CORTEX.DATA_AGENT_RUN SQL."""
    try:
        _ensure_warehouse()
        request_body = json.dumps({
            "messages": [
                {"role": "user",
                 "content": [{"type": "text", "text": question}]}
            ],
        })

        df = get_session().sql(
            "SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?)) AS RESP",
            params=[AGENT, request_body],
        ).to_pandas()

        raw = df["RESP"].iloc[0] if not df.empty and df["RESP"].iloc[0] else None
        body = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, dict) else {})

        answer_parts = []
        sql_text = ""
        content = body.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        answer_parts.append(item.get("text", ""))
                    elif item.get("type") == "tool_results":
                        for tc in item.get("content", []):
                            if isinstance(tc, dict) and tc.get("type") == "sql":
                                sql_text = tc.get("statement", "")
                    elif item.get("type") == "tool_use":
                        pass  # thinking / planning steps

        answer = "".join(answer_parts)

        return {
            "answer": answer,
            "sql": sql_text,
            "confidence": 0.85 if answer else 0.3,
            "error": None,
        }
    except Exception as e:
        return {"answer": "", "sql": "", "confidence": 0.0,
                "error": f"{type(e).__name__}: {e}"}


# -- Unified Router --------------------------------------------------------

def api_available() -> bool:
    """True when Cortex Analyst / Agent can be reached from this runtime."""
    return True


def api_unavailable_reason() -> str:
    return ""


def ask_agent(question: str, history: list = None,
              force_mode: str = None) -> dict:
    mode = force_mode or _route(question)

    if mode == "agent":
        r = query_cortex_agent(question)
        return {"mode": "agent", "answer": r["answer"],
                "results": [], "sql": r.get("sql", ""),
                "confidence": r["confidence"],
                "chart_hint": "bar", "error": r["error"]}
    if mode == "search":
        r = search_transcripts(question)
        return {"mode": "search", "answer": r["rag_answer"],
                "results": r["results"], "sql": "",
                "confidence": 0.85 if r["results"] else 0.2,
                "chart_hint": "table", "error": None}
    r = query_cortex_analyst(question, history)
    return {"mode": "analyst", "answer": r["answer"],
            "results": [], "sql": r["sql"],
            "confidence": r["confidence"],
            "chart_hint": r["chart_hint"], "error": r["error"]}


# -- RAG quality evaluation ------------------------------------------------

@st.cache_data(ttl=600, max_entries=50, show_spinner=False)
def evaluate_rag_response(question: str, answer: str, chunks: tuple) -> dict:
    ctx = "\n".join(chunks[:3])
    prompt = (
        "Score this RAG response 0.0-1.0 on three metrics. "
        'Return ONLY valid JSON: {"groundedness":X,"context_relevance":X,"answer_relevance":X}\n'
        f"Question: {question}\nContext: {ctx}\nAnswer: {answer}"
    )
    try:
        raw = _complete(prompt)
        raw = re.sub(r"```[a-z]*", "", raw).strip().strip("`")
        data = json.loads(raw)
        return {k: round(float(data.get(k, 0)), 2)
                for k in ("groundedness", "context_relevance", "answer_relevance")}
    except Exception:
        return {"groundedness": 0.0, "context_relevance": 0.0, "answer_relevance": 0.0}
