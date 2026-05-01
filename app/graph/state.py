from typing import List, Optional, Tuple, TypedDict


class AgentState(TypedDict, total=False):
    question: str

    intent: str
    actions: List[str]
    tables_hint: List[str]
    step: int

    retry: int
    max_retry: int

    answer: Optional[str]
    tables: List[str]
    columns: List[Tuple[str, str]]
    table_metadata: list
    column_metadata: list
    tool_results: list
    table_agent_message: dict
    column_agent_message: dict

    next: str
    done: bool
    error: Optional[str]

    router_reason: Optional[str]
    failed_step: Optional[str]
