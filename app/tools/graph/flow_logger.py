def log_stage(node: str, state: dict, phase: str, extra: str = ""):
    step = state.get("step", "?")
    actions = state.get("actions", [])
    total = len(actions) if isinstance(actions, list) else "?"
    msg = f"[FLOW] node={node} | step={step}/{total} | phase={phase}"
    if extra:
        msg += f" | {extra}"
    print(msg)
