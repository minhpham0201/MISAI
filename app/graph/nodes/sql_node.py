from app.tools.graph.flow_logger import log_stage


def sql_generator_node(state):
    log_stage("sql_generate", state, "enter")
    log_stage("sql_generate", state, "generate.start")
    # placeholder
    state["sql"] = "SELECT ..."
    state["next"] = "__end__"
    log_stage("sql_generate", state, "generate.done", "next=__end__")
    return state
