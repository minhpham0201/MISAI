from app.agents.supervisor import answer_out_of_scope,generate_answer, route_intent
from app.tools.graph.flow_logger import log_stage


def supervisor_node(state):
    log_stage("supervisor", state, "enter")

    if "actions" not in state:
        log_stage("supervisor", state, "intent.start")
        plan = route_intent(state["question"])

        state["intent"] = plan["intent"]
        state["actions"] = plan["actions"]
        state["tables_hint"] = plan["tables_hint"]
        state["router_reason"] = plan["reason"]
        state["step"] = 0

        log_stage(
            "supervisor",
            state,
            "intent.done",
            f"intent={state['intent']} actions={state['actions']}",
        )

        if state["intent"] == "out_of_scope":
            state["answer"] = answer_out_of_scope(state["question"])
            state["next"] = "__end__"
            state["done"] = True
            log_stage("supervisor", state, "out_of_scope.done", "next=__end__")
            return state

    actions = state["actions"]
    step = state.get("step", 0)

    if step >= len(actions):
        log_stage("supervisor", state, "answer.start")

        answer = generate_answer(
            question=state.get("question"),
            tables=state.get("table_metadata", []),
            columns=state.get("column_metadata", []),
            tool_results=state.get("tool_results", []),
            table_agent_message=state.get("table_agent_message", {}),
            column_agent_message=state.get("column_agent_message", {}),
        )

        state["answer"] = answer
        state["next"] = "__end__"
        state["done"] = True
        log_stage("supervisor", state, "answer.done", "next=__end__")
        return state

    state["next"] = actions[step]
    log_stage("supervisor", state, "route", f"next={state['next']}")
    return state
