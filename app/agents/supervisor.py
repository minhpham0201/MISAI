import json
import re
import unicodedata

from app.core.llm import get_llm


llm_json = get_llm(json_mode=True)
llm_text = get_llm(json_mode=False)


ALLOWED_ACTIONS = {
    "table_search",
    "column_search",
    "sql_generate",
}

ALLOWED_INTENTS = {
    "metadata",
    "general_knowledge",
    "out_of_scope",
}

ALLOWED_METADATA_TASKS = {
    "search",
    "column_count",
    "sql_generate",
}


INTENT_ROUTER_PROMPT = """
Ban la intent router cho AI assistant ve data warehouse.
Hay phan loai cau hoi cua user va quyet dinh buoc xu ly toi thieu.

Intent cho phep:
- metadata: cau hoi lien quan den bang, cot, metadata data warehouse, nghiep vu du lieu, hoac SQL tren data warehouse.
- general_knowledge: cau hoi co the tra loi bang kien thuc pho thong tinh ma LLM da biet, hoac cau hoi hop le ve vai tro/chuc nang cua assistant.
- out_of_scope: cau hoi tao lao, khong lien quan, hoac can thong tin realtime/tool ngoai pham vi data warehouse nhu ngay gio hien tai, thoi tiet, gia ca, tin tuc.

Metadata tasks:
- search: tim bang/cot/metadata thong thuong.
- column_count: user hoi mot bang co bao nhieu cot/column/field.
- sql_generate: user muon sinh SQL.

Rules:
- Neu cau hoi nhac den table/bang/column/cot/field/metadata/schema/data warehouse thi intent=metadata.
- Neu user hoi "bang A co bao nhieu cot" thi intent=metadata, metadata_task=column_count, actions=["table_search"].
- Neu user hoi "cot nao..." thi intent=metadata, actions=["column_search"].
- Neu khong ro can bang hay cot thi intent=metadata, actions=["table_search", "column_search"].
- Neu user muon SQL thi them "sql_generate" o cuoi actions.
- Neu hoi ngay gio hien tai, thoi tiet, gia ca, tin tuc realtime thi intent=out_of_scope.
- Neu hoi kien thuc chung hop le thi intent=general_knowledge.
- Neu cau hoi khong phu hop pham vi tro ly data warehouse thi intent=out_of_scope.

Return ONLY JSON:
{
  "intent": "metadata",
  "metadata_task": "search",
  "actions": ["table_search", "column_search"],
  "tables_hint": [],
  "reason": "short reason"
}
"""


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


DIRECT_ANSWER_PROMPT = """
Ban la assistant ho tro data warehouse.
Tra loi bang tieng Viet, ngan gon, dung trong tam.
Neu cau hoi khong lien quan den data warehouse nhung van la kien thuc pho thong hop le, ban co the tra loi.
Khong bia thong tin noi bo ve he thong neu khong duoc cung cap.
"""


def safe_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _normalize_text(text: str):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def _route_by_rules(question: str):
    q = _normalize_text(question)

    realtime_tokens = [
        "hom nay",
        "ngay may",
        "bay gio",
        "may gio",
        "thoi gian hien tai",
        "thoi tiet",
        "nhiet do",
        "gia vang",
        "gia usd",
        "tin tuc",
    ]
    if any(token in q for token in realtime_tokens):
        return {
            "intent": "out_of_scope",
            "metadata_task": "search",
            "actions": [],
            "tables_hint": [],
            "reason": "rule: realtime/out-of-scope question",
        }

    asks_column_count = (
        any(token in q for token in ["bao nhieu cot", "bao nhieu column", "bao nhieu field"])
        and any(token in q for token in ["bang", "table"])
    )
    if asks_column_count:
        return {
            "intent": "metadata",
            "metadata_task": "column_count",
            "actions": ["table_search"],
            "tables_hint": [],
            "reason": "rule: table column count question",
        }

    if any(token in q for token in ["cot", "column", "field"]):
        return {
            "intent": "metadata",
            "metadata_task": "search",
            "actions": ["column_search"],
            "tables_hint": [],
            "reason": "rule: column metadata question",
        }

    if any(token in q for token in ["bang", "table", "metadata", "schema", "data warehouse", "sql"]):
        actions = ["table_search"]
        metadata_task = "search"
        if "sql" in q:
            actions.append("sql_generate")
            metadata_task = "sql_generate"
        return {
            "intent": "metadata",
            "metadata_task": metadata_task,
            "actions": actions,
            "tables_hint": [],
            "reason": "rule: table/metadata question",
        }

    return None


def route_intent(question: str):
    rule_route = _route_by_rules(question)
    if rule_route:
        return rule_route

    res = llm_json.invoke(
        [
            {"role": "system", "content": INTENT_ROUTER_PROMPT},
            {"role": "user", "content": question},
        ]
    )

    data = safe_parse_json(res.content)
    if not data:
        return {
            "intent": "metadata",
            "metadata_task": "search",
            "actions": ["table_search", "column_search"],
            "tables_hint": [],
            "reason": "fallback: router parse failed",
        }

    intent = data.get("intent", "metadata")
    if intent not in ALLOWED_INTENTS:
        intent = "metadata"

    metadata_task = data.get("metadata_task", "search")
    if metadata_task not in ALLOWED_METADATA_TASKS:
        metadata_task = "search"

    actions = data.get("actions", [])
    actions = [a for a in actions if a in ALLOWED_ACTIONS]
    if intent == "metadata" and not actions:
        actions = ["table_search", "column_search"]

    tables_hint = data.get("tables_hint", [])
    if not isinstance(tables_hint, list):
        tables_hint = []

    return {
        "intent": intent,
        "metadata_task": metadata_task,
        "actions": actions,
        "tables_hint": tables_hint,
        "reason": data.get("reason", ""),
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


def answer_with_llm_knowledge(question: str):
    res = llm_text.invoke(
        [
            {"role": "system", "content": DIRECT_ANSWER_PROMPT},
            {"role": "user", "content": question},
        ]
    )
    return res.content.strip()


def answer_out_of_scope(question: str):
    return (
        "Mình được thiết kế để hỗ trợ các câu hỏi về data warehouse như bảng, cột, "
        "metadata và SQL. Câu hỏi này nằm ngoài phạm vi đó. "
        "Bạn có thể hỏi kiểu: 'bảng CUSTOMER có những thông tin gì?', "
        "'cột nào lưu số căn cước?', hoặc 'bảng DEPOSIT có bao nhiêu cột?'"
    )
