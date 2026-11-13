
from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.nodes import (
    inspect_schema_node,
    generate_sql_node,
    validate_sql_node,
    execute_query_node,
    reflection_node,
)


def route_after_validation(
    state: AgentState,
) -> Literal["execute", "end"]:

    if state.get("status") == "validated":
        return "execute"

    return "end"


def route_after_execution(
    state: AgentState,
) -> Literal["reflection", "end"]:

    if state.get("status") == "success":
        return "end"

    if (
        state.get("status") == "error"
        and state.get("retry_count", 0) < 3
    ):
        return "reflection"

    return "end"


def build_agent_graph():

    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node(
        "inspect_schema",
        inspect_schema_node
    )

    workflow.add_node(
        "generate_sql",
        generate_sql_node
    )

    workflow.add_node(
        "validate_sql",
        validate_sql_node
    )

    workflow.add_node(
        "execute_query",
        execute_query_node
    )

    workflow.add_node(
        "reflection",
        reflection_node
    )

    # Initial workflow
    workflow.add_edge(
        START,
        "inspect_schema"
    )

    workflow.add_edge(
        "inspect_schema",
        "generate_sql"
    )

    workflow.add_edge(
        "generate_sql",
        "validate_sql"
    )

    # Only validated SQL can execute
    workflow.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute": "execute_query",
            "end": END,
        },
    )

    # Success terminates; database errors enter reflection
    workflow.add_conditional_edges(
        "execute_query",
        route_after_execution,
        {
            "reflection": "reflection",
            "end": END,
        },
    )

    # Corrected SQL goes through generation and validation again
    workflow.add_edge(
        "reflection",
        "generate_sql"
    )

    return workflow.compile()


agent = build_agent_graph()
