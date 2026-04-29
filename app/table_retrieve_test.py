from app.services.vector_retriever import table_retriever
from app.services.metadata import TableMetadataStore

PATH = r"data\tables_metadata.json"
table_store = TableMetadataStore(PATH)
retriever = table_retriever()   

queries = [
    "tài khoản tiền gửi",
    "bảng khách hàng",
    "thông tin deposit",
    "customer information",
]

for q in queries:
    print("\n" + "="*50)
    print("QUERY:", q)

    results = retriever.retrieve(q)

    for r in results:
        table_data = table_store.get(r.metadata.get("table"))

        print("SCORE:", getattr(r, "score", None))

        print("TABLE:", table_data.get("table_name"))
        print("DESCRIPTION:", table_data.get("description"))
        print("BUSINESS TERMS:", table_data.get("business_terms"))
        print("GRANULARITY:", table_data.get("granularity"))
        print("TABLE TYPE:", table_data.get("table_type"))
        print("\n")
