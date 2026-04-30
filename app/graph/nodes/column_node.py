from app.agents.column_agent import run_column_agent
from app.tools.graph.flow_logger import log_stage


def column_search_node(state):
    log_stage("column_search", state, "enter")
    log_stage("column_search", state, "agent.start")
    working_state = run_column_agent(state)
    log_stage(
        "column_search",
        working_state,
        "agent.done",
        f"columns={working_state.get('columns', [])}",
    )
    state.update(working_state)
    state["step"] += 1
    state["next"] = "supervisor"
    log_stage("column_search", state, "exit", "next=supervisor")
    return state
