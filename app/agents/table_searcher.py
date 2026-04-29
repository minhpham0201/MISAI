from app.services.vector_retriever import table_retriever
from app.services.metadata import TableMetadataStore

PATH = r"data\tables_metadata.json"
table_store = TableMetadataStore(PATH)
retriever = table_retriever()


def table_searcher(state: dict):
    question = state["question"]

    results = retriever.retrieve(question)

    tables = []
    metadata = []

    for r in results:
        table_name = r.metadata.get("logical_table")

        if not table_name:
            continue

        full = table_store.get(table_name)

        tables.append(table_name)
        metadata.append(full)

    # remove duplicate
    tables = list(dict.fromkeys(tables))

    return {
        **state,
        "tables": tables,
        "table_metadata": metadata
    }