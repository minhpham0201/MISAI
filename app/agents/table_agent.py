import json
import re
import unicodedata
from app.core.llm import get_llm
from app.tools.metadata.count_columns_tool import count_columns_tool
from app.tools.retrieval.table_search_tool import table_search_tool
from app.tools.graph.flow_logger import log_stage


llm_json = get_llm(json_mode=True)
llm_text = get_llm(json_mode=False)


TABLE_AGENT_GOAL = (
    "Tìm các tập table set phù hợp để trả lời được câu user query"
)


TABLE_JUDGE_PROMPT = """
You are TableAgent.

Goal:
- Select relevant table candidates for the user question.
- Decide whether current retrieved tables are sufficient.
- If not sufficient, request one better retrieval query.

Return ONLY JSON:
{
  "enough": true,
  "reason": "short reason",
  "next_query": ""
}
"""


TABLE_REWRITE_PROMPT = """
You are TableAgent query rewriter.

Write a short retrieval query to find table metadata.
Output only one line of plain text.
"""


def _safe_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _normalize_text(text: str):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def _wants_column_count(question: str):
    q = _normalize_text(question or "")
    has_table_marker = any(token in q for token in ["bang", "table"])
    has_count_marker = any(
        token in q for token in ["bao nhieu cot", "bao nhieu column", "bao nhieu field", "dem so cot"]
    )
    return has_table_marker and has_count_marker


def _judge_table_candidates(question: str, candidates: list):
    payload = {
        "goal": TABLE_AGENT_GOAL,
        "question": question,
        "candidates": candidates,
    }
    res = llm_json.invoke([
        {"role": "system", "content": TABLE_JUDGE_PROMPT},
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


def _rewrite_table_query(question: str, candidates: list, reason: str):
    payload = {
        "goal": TABLE_AGENT_GOAL,
        "question": question,
        "candidates": candidates,
        "reason": reason,
    }
    res = llm_text.invoke([
        {"role": "system", "content": TABLE_REWRITE_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ])
    return res.content.strip()


def _to_debug_json(data: dict):
    return json.dumps(data, ensure_ascii=False, default=str)


def run_table_agent(state: dict):
    max_retry = 2
    attempt = 0
    working_state = {**state}
    trace = []
    final_judge = None
    final_candidates = []

    while attempt <= max_retry:
        log_stage(
            "table_agent",
            working_state,
            "retrieve.start",
            f"attempt={attempt} query={working_state.get('table_query') or working_state.get('question')}",
        )
        working_state = table_search_tool(working_state)
        candidates = working_state.get("table_candidates", [])
        log_stage(
            "table_agent",
            working_state,
            "retrieve.done",
            f"candidates={len(candidates)}",
        )
        log_stage("table_agent", working_state, "judge.start", f"attempt={attempt}")
        judge = _judge_table_candidates(
            question=working_state.get("question", ""),
            candidates=candidates,
        )
        final_judge = judge
        final_candidates = candidates
        log_stage(
            "table_agent",
            working_state,
            "judge.done",
            f"enough={judge['enough']} reason={judge['reason']}",
        )

        print(
            f"[TableAgent] attempt={attempt} | enough={judge['enough']} | reason={judge['reason']}"
        )
        print("Found tables:", working_state.get("tables", []))
        trace.append(
            {
                "attempt": attempt,
                "query": working_state.get("table_query_used"),
                "judge": judge,
                "tables": working_state.get("tables", []),
            }
        )

        if judge["enough"] or attempt == max_retry:
            break

        log_stage("table_agent", working_state, "rewrite.start", f"attempt={attempt}")
        next_query = judge["next_query"] or _rewrite_table_query(
            question=working_state.get("question", ""),
            candidates=candidates,
            reason=judge.get("reason", ""),
        )
        working_state["table_query"] = next_query
        log_stage("table_agent", working_state, "rewrite.done", f"next_query={next_query}")
        attempt += 1

    working_state["table_agent_trace"] = trace
    confidence = "high" if final_judge and final_judge.get("enough") else "low"
    working_state["table_agent_message"] = {
        "confidence": confidence,
        "reason": (final_judge or {}).get("reason", ""),
        "query_used": working_state.get("table_query_used"),
        "selected_tables": working_state.get("tables", []),
        "selected_candidates": final_candidates,
        "guidance": (
            "Ưu tiên dùng selected_tables cho câu trả lời."
            if confidence == "high"
            else "Độ chắc chắn thấp, chỉ dùng selected_tables như gợi ý tạm thời và nêu rõ cần xác minh thêm."
        ),
    }

    if _wants_column_count(working_state.get("question", "")):
        tables = working_state.get("tables", [])
        if not tables:
            tables = working_state.get("tables_hint", [])

        if tables:
            log_stage("table_agent", working_state, "count_columns.start", f"tables={tables}")
            result = count_columns_tool(tables)
            tool_results = list(working_state.get("tool_results", []))
            tool_results.append(result)
            working_state["tool_results"] = tool_results
            log_stage("table_agent", working_state, "count_columns.done", f"result={result}")
        else:
            log_stage("table_agent", working_state, "count_columns.skip", "no table found")

    log_stage(
        "table_agent",
        working_state,
        "confidence.done",
        f"confidence={confidence} reason={(final_judge or {}).get('reason', '')}",
    )
    debug_payload = {
        "confidence": confidence,
        "final_judge": final_judge or {},
        "query_used": working_state.get("table_query_used"),
        "selected_tables": working_state.get("tables", []),
        "selected_candidates": final_candidates,
        "trace": trace,
    }
    log_stage(
        "table_agent",
        working_state,
        "debug.snapshot",
        _to_debug_json(debug_payload),
    )
    log_stage("table_agent", working_state, "finish", f"attempts={len(trace)}")
    return working_state
