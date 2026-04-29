import chromadb
from dotenv import load_dotenv
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex


CHROMA_PATH = "data/chroma_db"
load_dotenv() 


# TABLE RETRIEVER
def table_retriever(similarity_top_k: int = 2):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection("table_metadata")

    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store)

    return index.as_retriever(similarity_top_k=similarity_top_k)

# COLUMN RETRIEVER
def column_retriever(similarity_top_k: int = 3):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection("column_metadata")

    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store)

    return index.as_retriever(similarity_top_k=similarity_top_k)