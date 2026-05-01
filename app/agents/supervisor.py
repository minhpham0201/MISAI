import re
import unicodedata

from app.core.llm import get_llm


llm_text = get_llm(json_mode=False)


ALLOWED_ACTIONS = {
    "table_search",
    "column_search",
    "sql_generate",
}

ALLOWED_INTENTS = {
    "metadata",
    "out_of_scope",
}


ANSWER_PROMPT = """
You are a data assistant.

Given:
- user question
- table metadata
- column metadata
- tool results

Explain clearly for business users.

Rules:
- Answer in Vietnamese
- Be concise but informative
- Mention table name and column name if relevant
- If tool results are available, use them as the primary source.
- If no info found, say you don't know
"""


def _normalize_text(text: str):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def _is_metadata_query(question: str):
    q = _normalize_text(question)
    markers = [
        "bang",
        "table",
        "cot",
        "column",
        "field",
        "metadata",
        "schema",
        "data warehouse",
        "sql",
        "record",
    ]
    return any(token in q for token in markers)


def _plan_metadata_actions(question: str):
    q = _normalize_text(question)
    has_table = any(token in q for token in ["bang", "table"])
    has_column = any(token in q for token in ["cot", "column", "field"])
    wants_sql = "sql" in q
    asks_count_columns = (
        any(token in q for token in ["bao nhieu cot", "bao nhieu column", "bao nhieu field", "dem so cot"])
        and has_table
    )

    if asks_count_columns:
        actions = ["table_search"]
    elif has_column and not has_table:
        actions = ["column_search"]
    elif has_table and not has_column:
        actions = ["table_search"]
    elif has_table and has_column:
        actions = ["table_search", "column_search"]
    else:
        actions = ["table_search", "column_search"]

    if wants_sql and "sql_generate" not in actions:
        actions.append("sql_generate")

    return actions


def route_intent(question: str):
    if _is_metadata_query(question):
        return {
            "intent": "metadata",
            "actions": _plan_metadata_actions(question),
            "tables_hint": [],
            "reason": "rule: metadata markers detected",
        }

    return {
        "intent": "out_of_scope",
        "actions": [],
        "tables_hint": [],
        "reason": "rule: non-metadata question",
    }


def generate_answer(question, tables, columns, tool_results=None):
    content = f"""
        User question:
        {question}

        Tables:
        {tables}

        Columns:
        {columns}

        Tool results:
        {tool_results or []}
        """
    res = llm_text.invoke(
        [
            {"role": "system", "content": ANSWER_PROMPT},
            {"role": "user", "content": content},
        ]
    )
    return res.content.strip()


def answer_out_of_scope(question: str):
    return (
        "Mình được thiết kế để hỗ trợ các câu hỏi về data warehouse như bảng, cột, metadata và SQL. "
        "Câu hỏi này chưa thuộc phạm vi đó. Bạn có thể hỏi kiểu: "
        "'bảng CUSTOMER có những thông tin gì?', "
        "'cột nào lưu số căn cước?', hoặc 'bảng DEPOSIT có bao nhiêu cột?'"
    )
