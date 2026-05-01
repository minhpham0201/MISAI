import streamlit as st

from app.graph.builder import build_graph


st.set_page_config(page_title="MISAI Agent", page_icon="🤖", layout="wide")


@st.cache_resource
def get_graph():
    return build_graph()


def run_agent(question: str):
    graph = get_graph()
    return graph.invoke({"question": question})


st.title("MISAI Agentic Assistant")
st.caption("Nhập câu hỏi về metadata bảng/cột, hệ thống sẽ chạy graph và trả kết quả.")

with st.form("ask_form", clear_on_submit=False):
    question = st.text_input(
        "Câu hỏi",
        placeholder="Ví dụ: bảng deposit có bao nhiêu cột?",
    )
    submitted = st.form_submit_button("Gửi", type="primary")

if submitted:
    if not question.strip():
        st.warning("Vui lòng nhập câu hỏi.")
    else:
        with st.spinner("Đang xử lý..."):
            try:
                result = run_agent(question.strip())
            except Exception as exc:
                st.error(f"Lỗi khi chạy agent: {exc}")
            else:
                st.subheader("Kết quả")
                st.write(result.get("answer") or "Không có câu trả lời.")

                with st.expander("Chi tiết debug"):
                    st.json(
                        {
                            "intent": result.get("intent"),
                            "actions": result.get("actions"),
                            "tables": result.get("tables"),
                            "columns": result.get("columns"),
                            "tool_results": result.get("tool_results"),
                            "table_agent_trace": result.get("table_agent_trace"),
                            "column_agent_trace": result.get("column_agent_trace"),
                        }
                    )
