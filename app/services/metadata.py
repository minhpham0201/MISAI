import json
from pathlib import Path


class TableMetadataStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self._data = self._load()

    def _load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # build lookup theo logical_name
        return {
            item["logical_name"]: item
            for item in data
        }

    # GET FULL TABLE
    def get(self, table_name: str):
        return self._data.get(table_name)

    # GET SELECTED FIELDS
    def get_fields(self, table_name: str, fields: list[str]):
        table = self.get(table_name)
        if not table:
            return None

        return {
            k: table[k]
            for k in fields
            if k in table
        }

    # GET ALL TABLES
    def all(self):
        return list(self._data.values())


class ColumnMetadataStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self._data = self._load()

    def _load(self):
        import json

        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # key = table, column
        return {
            (item["logical_table"], item["logical_column"]): item
            for item in data
        }

    # =========================
    # GET FULL COLUMN
    # =========================
    def get(self, table: str, column: str):
        return self._data.get((table, column))

    # =========================
    # GET FIELD
    # =========================
    def get_fields(self, table: str, column: str, fields: list[str]):
        col = self.get(table, column)
        if not col:
            return None

        return {
            k: col[k]
            for k in fields
            if k in col
        }

    # =========================
    # GET ALL COLUMN BY TABLE
    # =========================
    def get_by_table(self, table: str):
        return [
            v for (t, _), v in self._data.items()
            if t == table
        ]