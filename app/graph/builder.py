from langgraph.graph import StateGraph, END
from app.graph.state import AgentState

from app.graph.nodes.supervisor_node import supervisor_node
from app.graph.nodes.table_node import table_search_node
from app.graph.nodes.column_node import column_search_node
from app.graph.nodes.sql_node import sql_generator_node


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("table_search", table_search_node)
    builder.add_node("column_search", column_search_node)
    builder.add_node("sql_generate", sql_generator_node)

    builder.set_entry_point("supervisor")

    builder.add_conditional_edges(
        "supervisor",
        lambda state: state["next"],
        {
            "table_search": "table_search",
            "column_search": "column_search",
            "sql_generate": "sql_generate",
            "__end__": END,
        }
    )

    builder.add_edge("table_search", "supervisor")
    builder.add_edge("column_search", "supervisor")

    return builder.compile()