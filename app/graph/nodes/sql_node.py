def sql_generator_node(state):
    # placeholder
    state["sql"] = "SELECT ..."
    state["next"] = "__end__"
    return state