from app.agents.table_agent import run_table_agent
from app.tools.graph.flow_logger import log_stage


def table_search_node(state):
    log_stage("table_search", state, "enter")
    log_stage("table_search", state, "agent.start")
    working_state = run_table_agent(state)
    log_stage(
        "table_search",
        working_state,
        "agent.done",
        f"tables={working_state.get('tables', [])}",
    )
    state.update(working_state)
    state["step"] += 1
    state["next"] = "supervisor"
    log_stage("table_search", state, "exit", "next=supervisor")
    return state
