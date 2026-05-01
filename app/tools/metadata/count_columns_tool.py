from functools import lru_cache
from pathlib import Path

from app.services.metadata import ColumnMetadataStore


PATH = Path("data") / "columns_metadata.json"


@lru_cache(maxsize=1)
def get_column_store():
    return ColumnMetadataStore(PATH)


def count_columns_tool(table_names: list[str]) -> dict:
    store = get_column_store()
    results = []

    for table_name in table_names:
        normalized_table = table_name.upper()
        columns = store.get_by_table(normalized_table)
        unique_columns = sorted(
            {item.get("logical_column") for item in columns if item.get("logical_column")}
        )
        results.append(
            {
                "table": normalized_table,
                "document_count": len(columns),
                "unique_column_count": len(unique_columns),
                "columns": unique_columns,
            }
        )

    return {
        "tool": "count_columns_tool",
        "results": results,
    }
