import json
import shutil
import os
import chromadb
from dotenv import load_dotenv

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()

# CONFIG
TABLE_JSON = r"data\tables_metadata.json"
COLUMN_JSON = r"data\columns_metadata.json"
CHROMA_PATH = r"data\chroma_db"


# LOAD JSON
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# DROP CURRENT CHROMA DB
def drop_chroma_db():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print("Drop Chroma DB")

    os.makedirs(CHROMA_PATH, exist_ok=True)

# BUILD DOCUMENTS
def build_table_docs(data):
    docs = []

    for item in data:
        text = f"""
        Table: {item.get("logical_name")}
        Description: {item.get("description")}
        Business Terms: {", ".join(item.get("business_terms", []))}
        Granularity: {item.get("granularity", "")}
        Common Dimensions: {", ".join(item.get("common_dimensions", []))}
        """

        docs.append(
            Document(
                text=text,
                metadata={
                    "logical_table": item.get("logical_name")
                }
            )
        )

    return docs


def build_column_docs(data):
    docs = []

    for item in data:
        text = f"""
        Column: {item.get("logical_column")}
        Table: {item.get("logical_table")}
        Description: {item.get("description")}
        Business Terms: {", ".join(item.get("business_terms", []))}
        """

        docs.append(
            Document(
                text=text.strip(),
                metadata={
                    "logical_table": item.get("logical_table"),
                    "logical_column": item.get("logical_column")
                }
            )
        )

    return docs

# CREATE CHROMA DB
def create_chroma_index():
    # DROP existing collections
    drop_chroma_db()

    print("🚀 Loading JSON...")
    table_data = load_json(TABLE_JSON)
    column_data = load_json(COLUMN_JSON)

    print("📄 Building documents...")
    table_docs = build_table_docs(table_data)
    column_docs = build_column_docs(column_data)

    print("🔌 Connecting Chroma...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    # collections
    table_collection = chroma_client.get_or_create_collection("table_metadata")
    column_collection = chroma_client.get_or_create_collection("column_metadata")

    # vector stores
    table_store = ChromaVectorStore(chroma_collection=table_collection)
    column_store = ChromaVectorStore(chroma_collection=column_collection)

    # storage context
    table_ctx = StorageContext.from_defaults(vector_store=table_store)
    column_ctx = StorageContext.from_defaults(vector_store=column_store)

    print("🧠 Embedding & indexing...")

    VectorStoreIndex.from_documents(
        table_docs,
        storage_context=table_ctx,
    )

    VectorStoreIndex.from_documents(
        column_docs,
        storage_context=column_ctx,
    )

    table_count = table_collection.count()
    column_count = column_collection.count()
    print(f"Ingested in table_metadata: {table_count}")
    print(f"Ingested in column_metadata: {column_count}")
    print("DONE! Chroma DB created at:", CHROMA_PATH)


# MAIN
if __name__ == "__main__":
    create_chroma_index()
