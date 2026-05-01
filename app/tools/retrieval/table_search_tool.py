from app.services.vector_retriever import table_retriever
from app.services.metadata import TableMetadataStore


PATH = "data/tables_metadata.json"
table_store = TableMetadataStore(PATH)
retriever = table_retriever()


def table_search_tool(state: dict):
    question = state.get("table_query") or state["question"]

    results = retriever.retrieve(question)

    tables = []
    metadata = []
    candidates = []
    seen = set()

    for idx, r in enumerate(results, start=1):
        table_name = r.metadata.get("logical_table")
        score = getattr(r, "score", None)
        print(f"  rank={idx} | table={table_name} | confidence={score}")

        if not table_name:
            continue

        if table_name in seen:
            continue
        seen.add(table_name)

        full = table_store.get(table_name)
        if not full:
            continue

        tables.append(table_name)
        metadata.append(full)
        candidates.append(
            {
                "table": table_name,
                "score": score,
            }
        )

    return {
        **state,
        "tables": tables,
        "table_metadata": metadata,
        "table_query_used": question,
        "table_candidates": candidates,
    }
