from app.agents.supervisor import call_llm_plan, generate_answer

def supervisor_node(state):

    # =========================
    # PLAN (only once)
    # =========================
    if "actions" not in state:
        plan = call_llm_plan(state["question"])

        state["actions"] = plan["actions"]
        state["tables_hint"] = plan["tables_hint"]
        state["step"] = 0

        print("🧠 PLAN:", state["actions"])

    actions = state["actions"]
    step = state.get("step", 0)

    # =========================
    # FINISH → GENERATE ANSWER
    # =========================
    if step >= len(actions):
        print("🧠 Generating final answer...")

        answer = generate_answer(
            question=state.get("question"),
            tables=state.get("table_metadata", []),
            columns=state.get("column_metadata", [])
        )

        state["answer"] = answer
        state["next"] = "__end__"
        state["done"] = True
        return state

    # =========================
    # ROUTE
    # =========================
    state["next"] = actions[step]
    return state