from app.services.vector_retriever import column_retriever
from app.services.metadata import ColumnMetadataStore


PATH = "data/columns_metadata.json"
column_store = ColumnMetadataStore(PATH)
retriever = column_retriever()


def column_search_tool(state: dict):
    question = state.get("column_query") or state["question"]
    tables = state.get("tables", [])

    results = retriever.retrieve(question)

    columns = []
    metadata = []
    candidates = []
    seen = set()

    for r in results:
        table = r.metadata.get("logical_table")
        column = r.metadata.get("logical_column")
        score = getattr(r, "score", None)

        if not table or not column:
            continue

        # Filter by selected tables from table_search phase.
        if tables and table not in tables:
            continue

        full = column_store.get(table, column)
        if not full:
            continue

        key = (table, column)
        if key in seen:
            continue
        seen.add(key)

        columns.append(key)
        metadata.append(full)
        candidates.append(
            {
                "table": table,
                "column": column,
                "score": score,
            }
        )

    return {
        **state,
        "columns": columns,
        "column_metadata": metadata,
        "column_query_used": question,
        "column_candidates": candidates,
    }
