
from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    # User request
    user_query: str

    # Database metadata
    schema_info: dict[str, Any]
    schema_text: str

    # SQL generation
    generated_sql: str
    correction_feedback: str

    # SQL execution
    db_result: list[dict[str, Any]]
    columns: list[str]
    row_count: int

    # Error handling
    error_message: str
    error_type: str
    retry_count: int

    # Execution status
    status: str

    # Transparent execution history
    logs: list[str]
