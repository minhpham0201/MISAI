from typing import TypedDict, List, Tuple, Optional


class AgentState(TypedDict, total=False):
    # input
    question: str

    # planning
    actions: List[str]
    step: int

    # retry
    retry: int
    max_retry: int

    # results
    answer: Optional[str]
    tables: List[str]
    columns: List[Tuple[str, str]]

    table_metadata: list
    column_metadata: list

    # control
    next: str
    done: bool
    error: Optional[str]

    # debug
    failed_step: Optional[str]