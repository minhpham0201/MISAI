from app.core.llm import get_llm

llm = get_llm()

SYSTEM_PROMPT = """
You are a SQL expert.

Given:
- user question
- list of tables
- list of columns

Write a correct SQL query.

Rules:
- Use only provided tables/columns
- Use proper JOIN if needed
- Return ONLY SQL (no explanation)
"""


def sql_generator(state):
    question = state["question"]
    tables = state.get("tables", [])
    columns = state.get("columns", [])

    context = f"""
Tables:
{tables}

Columns:
{columns}

Question:
{question}
"""

    res = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": context}
    ])

    return {
        "answer": res.content
    }