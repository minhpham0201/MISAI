import re
import unicodedata
import json

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
    "out_of_scope",
}


ANSWER_PROMPT = """
bạn là agent trả lời cho người dùng các câu hỏi về metadata của data warehouse

Input:
- user input
- table metadata
- column metadata
- tool results

Giải thích dưới góc độ business users.

Rules:
- Trả lời bằng tiếng Việt
- Ngắn gọn nhưng đủ thông tin cần thiết
- Chỉ dùng thông tin có liên quan trực tiếp đến câu hỏi
- Không giải thích quy trình nội bộ, không nhắc đến RAG/candidate/ranking/confidence cho người dùng cuối
- Không liệt kê bảng/cột chỉ để "tham khảo" khi chưa đủ chắc chắn
- Ưu tiên làm theo nhận định của table agent và column agent về độ chắc chắn kết quả
- Nếu confidence thấp hoặc có dấu hiệu chưa đủ dữ liệu thì trả lời "chưa đủ thông tin để xác định chính xác"
- Nếu không đủ thông tin, hãy trả lời không đủ thông tin để trả lời thay vì đoán bừa
"""


INTENT_CLASSIFY_PROMPT = """
Bạn là intent router cho trợ lý metadata data warehouse.

Nhiệm vụ:
- Phân loại câu hỏi người dùng thành một trong 2 intent:
  1) metadata: hỏi cách tìm/ý nghĩa/vị trí dữ liệu trong hệ thống DWH, bảng, cột, schema, SQL, mapping field business
  2) out_of_scope: không liên quan metadata DWH

Ví dụ thuộc metadata:
- "địa chỉ khách hàng nằm ở đâu trong hệ thống"
- "nên xem bảng nào để lấy số điện thoại"
- "field nào lưu trạng thái hợp đồng"
- "cho mình SQL lấy danh sách khách hàng"

Trả về JSON duy nhất:
{
  "intent": "metadata",
  "reason": "short reason"
}
"""


def _normalize_text(text: str):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def _safe_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None

# Cách này sẽ giúp route nhanh theo rule, nếu ko trả ra thì sẽ gọi xuống LLM bên dưới
# Sẽ bị false negative: nếu user có keyword trùng như rule nhưng thực ra là out of scope
def _is_metadata_query(question: str):
    q = _normalize_text(question)
    explicit_markers = [
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
    if any(token in q for token in explicit_markers):
        return True

    discovery_verbs = [
        "tim",
        "kiem",
        "tra cuu",
        "coi",
        "xem",
        "lay",
        "co the lay",
        "o dau",
        "nam o dau",
    ]
    business_entities = [
        "khach hang",
        "hop dong",
        "tai khoan",
        "giao dich",
        "du no",
        "tien gui", "tien vay", "pay"
    ]
    system_context = ["he thong", "dwh", "kho du lieu", "warehouse"]

    has_discovery_intent = any(token in q for token in discovery_verbs)
    has_business_entity = any(token in q for token in business_entities)
    has_system_context = any(token in q for token in system_context)

    return has_discovery_intent and (has_business_entity or has_system_context)


def _route_intent_with_llm(question: str):
    res = llm_json.invoke(
        [
            {"role": "system", "content": INTENT_CLASSIFY_PROMPT},
            {"role": "user", "content": question},
        ]
    )
    data = _safe_parse_json(res.content)
    if not data:
        return None

    intent = data.get("intent")
    if intent not in ALLOWED_INTENTS:
        return None

    return {
        "intent": intent,
        "actions": _plan_metadata_actions(question) if intent == "metadata" else [],
        "tables_hint": [],
        "reason": f"llm: {data.get('reason', '').strip() or 'classified'}",
    }


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

    llm_plan = _route_intent_with_llm(question)
    if llm_plan:
        return llm_plan

    return {
        "intent": "out_of_scope",
        "actions": [],
        "tables_hint": [],
        "reason": "fallback: non-metadata question",
    }


def generate_answer(
    question,
    tables,
    columns,
    tool_results=None,
    table_agent_message=None,
    column_agent_message=None,
):
    table_conf = (table_agent_message or {}).get("confidence", "")
    column_conf = (column_agent_message or {}).get("confidence", "")

    # Chỉ chuyển metadata có độ chắc chắn cao để tránh câu trả lời bị nhiễu.
    safe_tables = tables if table_conf == "high" else []
    safe_columns = columns if column_conf == "high" else []

    confidence_gate = {
        "table_confidence": table_conf or "unknown",
        "column_confidence": column_conf or "unknown",
        "tables_used": bool(safe_tables),
        "columns_used": bool(safe_columns),
    }

    content = f"""
        User question:
        {question}

        Tables:
        {safe_tables}

        Columns:
        {safe_columns}

        Table agent message:
        {table_agent_message or {}}

        Column agent message:
        {column_agent_message or {}}

        Confidence gate:
        {confidence_gate}

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
