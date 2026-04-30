from app.agents.supervisor import call_llm_plan, generate_answer
from app.tools.graph.flow_logger import log_stage


def supervisor_node(state):
    log_stage("supervisor", state, "enter")

    # PLAN (only once)
    if "actions" not in state:
        log_stage("supervisor", state, "plan.start")
        plan = call_llm_plan(state["question"])

        state["actions"] = plan["actions"]
        state["tables_hint"] = plan["tables_hint"]
        state["step"] = 0

        log_stage("supervisor", state, "plan.done", f"actions={state['actions']}")

    actions = state["actions"]
    step = state.get("step", 0)

    # FINISH -> GENERATE ANSWER
    if step >= len(actions):
        log_stage("supervisor", state, "answer.start")

        answer = generate_answer(
            question=state.get("question"),
            tables=state.get("table_metadata", []),
            columns=state.get("column_metadata", []),
        )

        state["answer"] = answer
        state["next"] = "__end__"
        state["done"] = True
        log_stage("supervisor", state, "answer.done", "next=__end__")
        return state

    # ROUTE
    state["next"] = actions[step]
    log_stage("supervisor", state, "route", f"next={state['next']}")
    return state
