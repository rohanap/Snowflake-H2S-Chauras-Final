"""
utils/rag_agent.py
Unified agent routing to Cortex Search (transcripts),
Cortex Analyst (Customer 360 metrics), or the Cortex Agent object
for INSURANCE_C360.
"""
import json, re
import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import _snowflake

DB      = "INSURANCE_C360"
SCHEMA  = "SILVER"
SERVICE = "TRANSCRIPT_SEARCH"
SEM_MDL = f"{DB}.GOLD.CUSTOMER_360_SEMANTIC"
AGENT   = f"{DB}.GOLD.INSURANCE_C360_AGENT"

_TRANSCRIPT_KW = [
    "call","transcript","said","complained","mentioned","conversation",
    "spoke","told","agent","discussed","upset","cancell","claim status",
    "unhappy","resolved","sentiment","quote","customer said",
]
_METRIC_KW = [
    "how many","count","average","total","sum","percent","rate",
    "by segment","by state","by income","by city","by policy","compare",
    "trend","revenue","premium","ltv","lifetime value","churn risk",
    "highest","lowest","most","least","distribution","breakdown",
]

def _route(question: str) -> str:
    q = question.lower()
    s = sum(1 for kw in _TRANSCRIPT_KW if kw in q)
    m = sum(1 for kw in _METRIC_KW    if kw in q)
    return "search" if s >= m else "analyst"


# -- Cortex Search -------------------------------------------------------

def search_transcripts(query: str, limit: int = 5,
                       customer_filter: str = None) -> dict:
    session = get_active_session()
    root    = Root(session)
    svc     = (root.databases[DB]
                   .schemas[SCHEMA]
                   .cortex_search_services[SERVICE])

    filt = {}
    if customer_filter:
        filt = {"@eq": {"CUSTOMER_ID": customer_filter}}

    resp    = svc.search(
        query=query,
        columns=["CALL_ID","CUSTOMER_ID","CUSTOMER_NAME","INTERACTION_DATE",
                 "CHANNEL","SUBJECT","TRANSCRIPT_TEXT","CALL_SUMMARY",
                 "SENTIMENT_SCORE","CUSTOMER_INTENT","KEY_TOPICS","SEGMENT"],
        filter=filt if filt else None,
        limit=limit,
    )
    results = resp.results if hasattr(resp, "results") else []

    rag_answer = ""
    if results:
        context = "\n\n---\n\n".join([
            f"Customer: {r.get('CUSTOMER_NAME','')}\n"
            f"Date: {str(r.get('INTERACTION_DATE',''))[:10]}\n"
            f"Subject: {r.get('SUBJECT','')}\n"
            f"Summary: {r.get('CALL_SUMMARY','')}"
            for r in results[:3]
        ])
        prompt = (
            "You are an insurance customer insights analyst. "
            "Answer the question using ONLY the call context below. "
            "Be concise and specific. "
            f"If the answer is not in the context say so.\n\n"
            f"CONTEXT:\n{context}\n\nQUESTION: {query}"
        ).replace("'","''")
        res = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large3','{prompt}') AS A
        """).to_pandas()
        rag_answer = res["A"].iloc[0] if not res.empty else ""
    else:
        rag_answer = "No matching transcripts found."

    return {"results": results, "rag_answer": rag_answer}


# -- Cortex Analyst --------------------------------------------------------

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
                              "content": [{"type":"text","text":text}]})
    messages.append({"role":"user",
                     "content":[{"type":"text","text":question}]})
    try:
        resp = _snowflake.send_snow_api_request(
            "POST", "/api/v2/cortex/analyst/message", {}, {},
            {"messages": messages, "semantic_view": SEM_MDL},
            None, 48000,
        )

        if isinstance(resp, dict):
            status = resp.get("status", 200)
            content = resp.get("content", "")
        else:
            status = 200
            content = resp

        if isinstance(content, str):
            body = json.loads(content)
        elif isinstance(content, dict):
            body = content
        else:
            body = {}

        if isinstance(body, str):
            body = json.loads(body)

        if status >= 400 or (isinstance(body, dict) and body.get("error_code")):
            err_msg = body.get("message", f"API error (status {status})")
            return {"sql":"","answer":"","chart_hint":"bar",
                    "confidence":0.0,"error": err_msg}

        sql_text = answer_text = ""
        message = body.get("message", {})

        if isinstance(message, str):
            answer_text = message
        elif isinstance(message, dict):
            msg_content = message.get("content", [])
            if isinstance(msg_content, str):
                answer_text = msg_content
            elif isinstance(msg_content, list):
                for item in msg_content:
                    if isinstance(item, str):
                        answer_text += item
                    elif isinstance(item, dict):
                        if item.get("type") == "sql":
                            sql_text = item.get("statement", "")
                        elif item.get("type") == "text":
                            answer_text = item.get("text", "")
                        elif item.get("type") == "suggestions":
                            pass
        elif isinstance(message, list):
            for item in message:
                if isinstance(item, dict):
                    if item.get("type") == "sql":
                        sql_text = item.get("statement", "")
                    elif item.get("type") == "text":
                        answer_text = item.get("text", "")

        if not sql_text and answer_text:
            sql_match = re.search(r"```sql\s*(.*?)\s*```", answer_text, re.DOTALL)
            if sql_match:
                sql_text = sql_match.group(1).strip()
                answer_text = re.sub(
                    r"```sql\s*.*?\s*```", "", answer_text, flags=re.DOTALL
                ).strip()

        ql = question.lower()
        if any(w in ql for w in ["trend","over time","monthly"]):
            chart = "line"
        elif any(w in ql for w in ["by segment","by state","by policy","compare","breakdown"]):
            chart = "bar"
        elif any(w in ql for w in ["share","distribution","proportion","percent"]):
            chart = "pie"
        else:
            chart = "bar"

        return {"sql": sql_text, "answer": answer_text,
                "chart_hint": chart, "confidence": 0.9 if sql_text else 0.3,
                "error": None}
    except Exception as e:
        return {"sql":"","answer":"","chart_hint":"bar",
                "confidence":0.0,"error":f"{type(e).__name__}: {e}"}


# -- Cortex Agent (native object) -----------------------------------------

def query_cortex_agent(question: str) -> dict:
    """Call the INSURANCE_C360_AGENT Cortex Agent object via REST API.
    This combines Cortex Analyst + Cortex Search in a single orchestrated call."""
    try:
        resp = _snowflake.send_snow_api_request(
            "POST",
            f"/api/v2/databases/{DB}/schemas/GOLD/agents/INSURANCE_C360_AGENT:run",
            {}, {},
            {
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": question}]}
                ]
            },
            None, 60000,
        )

        if isinstance(resp, dict):
            status = resp.get("status", 200)
            content = resp.get("content", "")
        else:
            status = 200
            content = resp

        if isinstance(content, str):
            # Agent returns SSE stream; parse text events
            answer_parts = []
            sql_text = ""
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("data:"):
                    try:
                        event = json.loads(line[5:].strip())
                        delta = event.get("delta", {})
                        if delta.get("type") == "text":
                            answer_parts.append(delta.get("text", ""))
                        elif delta.get("type") == "tool_results":
                            tool_content = delta.get("content", [])
                            for tc in tool_content:
                                if isinstance(tc, dict) and tc.get("type") == "sql":
                                    sql_text = tc.get("statement", "")
                    except json.JSONDecodeError:
                        if line.startswith("data:") and len(line) > 6:
                            answer_parts.append(line[5:].strip())
            answer = "".join(answer_parts)
        elif isinstance(content, dict):
            msg = content.get("message", {})
            msg_content = msg.get("content", []) if isinstance(msg, dict) else []
            answer = ""
            sql_text = ""
            for item in (msg_content if isinstance(msg_content, list) else []):
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        answer += item.get("text", "")
                    elif item.get("type") == "sql":
                        sql_text = item.get("statement", "")
        else:
            answer = str(content)
            sql_text = ""

        return {
            "answer": answer,
            "sql": sql_text,
            "confidence": 0.85,
            "error": None if status < 400 else f"Agent returned status {status}"
        }
    except Exception as e:
        return {"answer": "", "sql": "", "confidence": 0.0,
                "error": f"{type(e).__name__}: {e}"}


# -- Unified Router --------------------------------------------------------

def ask_agent(question: str, history: list = None,
              force_mode: str = None) -> dict:
    mode = force_mode or _route(question)

    if mode == "agent":
        r = query_cortex_agent(question)
        return {"mode": "agent", "answer": r["answer"],
                "results": [], "sql": r.get("sql", ""),
                "confidence": r["confidence"],
                "chart_hint": "bar", "error": r["error"]}
    elif mode == "search":
        r = search_transcripts(question)
        return {"mode":"search","answer":r["rag_answer"],
                "results":r["results"],"sql":"",
                "confidence":0.85 if r["results"] else 0.2,
                "chart_hint":"table","error":None}
    else:
        r = query_cortex_analyst(question, history)
        return {"mode":"analyst","answer":r["answer"],
                "results":[],"sql":r["sql"],
                "confidence":r["confidence"],
                "chart_hint":r["chart_hint"],"error":r["error"]}


# -- RAG quality evaluation ------------------------------------------------

def evaluate_rag_response(question: str, answer: str,
                           chunks: list) -> dict:
    session = get_active_session()
    ctx = "\n".join([c.get("CALL_SUMMARY","") for c in chunks[:3]])
    prompt = (
        "Score this RAG response 0.0-1.0 on three metrics. "
        "Return ONLY valid JSON: {\"groundedness\":X,\"context_relevance\":X,\"answer_relevance\":X}\n"
        f"Question: {question}\nContext: {ctx}\nAnswer: {answer}"
    ).replace("'","''")
    try:
        raw  = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large3','{prompt}') AS E
        """).to_pandas()["E"].iloc[0]
        raw  = re.sub(r"```[a-z]*","",raw).strip().strip("`")
        data = json.loads(raw)
        return {k: round(float(data.get(k,0)),2)
                for k in ("groundedness","context_relevance","answer_relevance")}
    except Exception:
        return {"groundedness":0.0,"context_relevance":0.0,"answer_relevance":0.0}
