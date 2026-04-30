import json
from app.core.llm import get_llm
from app.tools.retrieval.column_search_tool import column_search_tool
from app.tools.graph.flow_logger import log_stage


llm_json = get_llm(json_mode=True)
llm_text = get_llm(json_mode=False)


COLUMN_AGENT_GOAL = (
    "Find the most relevant columns for the user's analytics question."
)


COLUMN_JUDGE_PROMPT = """
You are ColumnAgent.

Goal:
- Select relevant column candidates for the user question.
- Decide whether current retrieved columns are sufficient.
- If not sufficient, request one better retrieval query.

Return ONLY JSON:
{
  "enough": true,
  "reason": "short reason",
  "next_query": ""
}
"""


COLUMN_REWRITE_PROMPT = """
You are ColumnAgent query rewriter.

Write a short retrieval query to find column metadata.
Output only one line of plain text.
"""


def _safe_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _judge_column_candidates(question: str, candidates: list):
    payload = {
        "goal": COLUMN_AGENT_GOAL,
        "question": question,
        "candidates": candidates,
    }
    res = llm_json.invoke([
        {"role": "system", "content": COLUMN_JUDGE_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ])
    data = _safe_parse_json(res.content)
    if not data:
        return {
            "enough": bool(candidates),
            "reason": "fallback: judge parse failed",
            "next_query": "",
        }
    return {
        "enough": bool(data.get("enough", False)),
        "reason": data.get("reason", ""),
        "next_query": (data.get("next_query") or "").strip(),
    }


def _rewrite_column_query(question: str, candidates: list, reason: str):
    payload = {
        "goal": COLUMN_AGENT_GOAL,
        "question": question,
        "candidates": candidates,
        "reason": reason,
    }
    res = llm_text.invoke([
        {"role": "system", "content": COLUMN_REWRITE_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ])
    return res.content.strip()


def run_column_agent(state: dict):
    max_retry = 2
    attempt = 0
    working_state = {**state}
    trace = []

    while attempt <= max_retry:
        log_stage(
            "column_agent",
            working_state,
            "retrieve.start",
            f"attempt={attempt} query={working_state.get('column_query') or working_state.get('question')}",
        )
        working_state = column_search_tool(working_state)
        candidates = working_state.get("column_candidates", [])
        log_stage(
            "column_agent",
            working_state,
            "retrieve.done",
            f"candidates={len(candidates)}",
        )
        log_stage("column_agent", working_state, "judge.start", f"attempt={attempt}")
        judge = _judge_column_candidates(
            question=working_state.get("question", ""),
            candidates=candidates,
        )
        log_stage(
            "column_agent",
            working_state,
            "judge.done",
            f"enough={judge['enough']} reason={judge['reason']}",
        )

        print(
            f"[ColumnAgent] attempt={attempt} | enough={judge['enough']} | reason={judge['reason']}"
        )
        print("Found columns:", working_state.get("columns", []))
        trace.append(
            {
                "attempt": attempt,
                "query": working_state.get("column_query_used"),
                "judge": judge,
                "columns": working_state.get("columns", []),
            }
        )

        if judge["enough"] or attempt == max_retry:
            break

        log_stage("column_agent", working_state, "rewrite.start", f"attempt={attempt}")
        next_query = judge["next_query"] or _rewrite_column_query(
            question=working_state.get("question", ""),
            candidates=candidates,
            reason=judge.get("reason", ""),
        )
        working_state["column_query"] = next_query
        log_stage("column_agent", working_state, "rewrite.done", f"next_query={next_query}")
        attempt += 1

    working_state["column_agent_trace"] = trace
    log_stage("column_agent", working_state, "finish", f"attempts={len(trace)}")
    return working_state
