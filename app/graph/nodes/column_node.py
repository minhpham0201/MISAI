from app.agents.column_searcher import column_searcher

def column_search_node(state):
   
    state = column_searcher(state)

    if not state.get("columns"):
        print("⚠️ No columns found (no retry mode)")

    print("🔍 Found columns:", state.get("columns"))
    state["step"] += 1
    state["next"] = "supervisor"
    return state
