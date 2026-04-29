from app.services.vector_retriever import column_retriever
from app.services.metadata import ColumnMetadataStore

PATH = r"data\columns_metadata.json"
column_store = ColumnMetadataStore(PATH)
retriever = column_retriever()

queries = [
    "cột nào trong bảng Deposit liên quan đến mã tài khoản khách hàng",
    "Cột Value_dt trong bảng Deposit là gì",
    "Cột thôn tin nào nói về địa chỉ khách hàng"
]

for q in queries:
    print("\n" + "="*70)
    print("QUERY:", q)

    results = retriever.retrieve(q)

    for r in results:
        column_data = column_store.get(table=r.metadata.get("table"), column=r.metadata.get("column"))

        print("SCORE:", getattr(r, "score", None))

        print("COLUMN:", column_data.get("column_name"))
        print("TABLE:", column_data.get("table"))
        print("DESCRIPTION:", column_data.get("description"))
        print("BUSINESS TERMS:", column_data.get("business_terms"))
        print("\n")
