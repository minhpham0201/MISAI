from app.agents.supervisor import call_llm_plan
import time


TEST_CASES = [
    "bảng Deposit dùng để làm gì",

    "Cột dbt_group_max có ý nghĩa là",

    "cột Value_dt trong bảng deposit là gì",
    "tabel nào chứa thông tin địa chỉ MAC của khách hàng",

    # ---- SQL
    "Lấy ra top 10 danh sách khách hàng gửi tiết kiệm trên 1 tỷ",
]


def run_tests():
    for q in TEST_CASES:
        result = call_llm_plan(q)

        print("=" * 60)
        print("QUESTION:", q)
        print("ACTIONS:", result["actions"])
        print("TABLE HINT:", result["tables_hint"])

        time.sleep(1)


if __name__ == "__main__":
    run_tests()