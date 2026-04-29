from app.agents.table_searcher import table_searcher

def table_search_node(state):
    state = table_searcher(state)

    if not state.get("tables"):
        print("⚠️ No tables found (no retry mode)")

    state["step"] += 1
    state["next"] = "supervisor"
    return state