import json
from app.core.llm import get_llm

# =========================
# LLM
# =========================
llm = get_llm(json_mode=True)

# =========================
# CONFIG
# =========================
ALLOWED_ACTIONS = {
    "table_search",
    "column_search",
    "sql_generate"
}

# =========================
# PROMPT: PLANNER
# =========================
SYSTEM_PROMPT = """
You are a strict query planner.

Given a user question, decide the MINIMAL sequence of actions needed.

Available actions:
- table_search
- column_search
- sql_generate

Rules:
- Only include necessary steps
- If user only asks about tables → ["table_search"]
- If user asks about columns without table → ["table_search", "column_search"]
- If user already specifies table → ["column_search"]
- If user wants SQL → include "sql_generate" at the end
- Return ONLY JSON

Output:
{
  "actions": ["table_search", "column_search"],
  "tables_hint": []
}
"""

# =========================
# PROMPT: REWRITE (future use)
# =========================
REWRITE_PROMPT = """
Rewrite the user question into a concise search query for retrieving database schema.

Rules:
- Keep only important keywords
- Include business terms if possible
- Remove filler words
- Output only text
"""

# =========================
# HELPERS
# =========================
def safe_parse_json(text: str):
    try:
        return json.loads(text)
    except:
        return None


# =========================
# MAIN: PLAN
# =========================
def call_llm_plan(question: str):
    res = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ])

    data = safe_parse_json(res.content)

    if not data:
        return {
            "actions": ["table_search", "column_search"],
            "tables_hint": []
        }

    actions = data.get("actions", [])
    tables_hint = data.get("tables_hint", [])

    # validate actions
    actions = [a for a in actions if a in ALLOWED_ACTIONS]

    if not actions:
        actions = ["table_search", "column_search"]

    if not isinstance(tables_hint, list):
        tables_hint = []

    return {
        "actions": actions,
        "tables_hint": tables_hint
    }


# =========================
# OPTIONAL: REWRITE (future retry)
# =========================
def rewrite_query(question: str):
    res = llm.invoke([
        {"role": "system", "content": REWRITE_PROMPT},
        {"role": "user", "content": question}
    ])

    return res.content.strip()


ANSWER_PROMPT = """
You are a data assistant.

Given:
- user question
- table metadata
- column metadata

Explain clearly for business users.

Rules:
- Answer in Vietnamese
- Be concise but informative
- Mention table name and column name if relevant
- If no info found, say you don't know
"""

def generate_answer(question, tables, columns):
    content = f"""
        User question:
        {question}

        Tables:
        {tables}

        Columns:
        {columns}
        """
    res = llm.invoke([
        {"role": "system", "content": ANSWER_PROMPT},
        {"role": "user", "content": content}
    ])

    return res.content.strip()