from app.services.vector_retriever import column_retriever
from app.services.metadata import ColumnMetadataStore

PATH = r"data\columns_metadata.json"

column_store = ColumnMetadataStore(PATH)
retriever = column_retriever()


def column_searcher(state: dict):
    question = state["question"]
    tables = state.get("tables", []) 

    results = retriever.retrieve(question)
    
    columns = []
    metadata = []

    for r in results:
        table = r.metadata.get("logical_table")
        column = r.metadata.get("logical_column")

        if not table or not column:
            continue

        # filter theo table (rất quan trọng khi narrow down từ table searcher)
        if tables and table not in tables:
            continue

        full = column_store.get(table, column)

        if not full:
            continue

        columns.append((table, column))
        metadata.append(full)

    # remove duplicate
    columns = list(dict.fromkeys(columns))

    return {
        **state,
        "columns": columns,
        "column_metadata": metadata
    }