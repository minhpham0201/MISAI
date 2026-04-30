from app.graph.builder import build_graph

def run_test(question: str):
    graph = build_graph()

    result = graph.invoke({
        "question": question
    })

    print("\n" + "=" * 60)
    print("QUESTION:", question)
    print("=" * 60)

    if "table_metadata" in result:
        print("\nTABLE METADATA:")
        for t in result["table_metadata"]:
            print("-", t.get("logical_name"))

    if "column_metadata" in result:
        print("\nCOLUMN METADATA:")
        for c in result["column_metadata"]:
            print("-", c.get("logical_table"), c.get("logical_column"))

    print("\nANSWER:")
    print(result.get("answer"))

if __name__ == "__main__":
    run_test("số dư tài khoản khách hàng được lưu ở đâu")


    