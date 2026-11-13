
from app.agent.graph import agent
from app.security.guardrails import (
    NeMoInputGuard,
    InputSecurityError,
)

# Initialize once and reuse across requests.
input_guard = NeMoInputGuard()


def run_agent(user_query: str):

    try:
        validated_query = input_guard.validate_input(user_query)

    except InputSecurityError as error:
        return {
            "status": "blocked",
            "generated_sql": None,
            "results": [],
            "columns": [],
            "row_count": 0,
            "retry_count": 0,
            "error": str(error),
            "logs": [
                "NeMo Guardrails blocked the request before SQL generation."
            ],
        }

    initial_state = {
        "user_query": validated_query,
        "retry_count": 0,
        "correction_feedback": "",
        "logs": ["NeMo input validation passed."],
        "status": "processing",
        "db_result": [],
        "columns": [],
        "row_count": 0,
        "error_message": "",
        "error_type": "",
    }

    result = agent.invoke(initial_state)

    return {
        "status": result.get("status"),
        "generated_sql": result.get("generated_sql"),
        "results": result.get("db_result", []),
        "columns": result.get("columns", []),
        "row_count": result.get("row_count", 0),
        "retry_count": result.get("retry_count", 0),
        "error": result.get("error_message"),
        "logs": result.get("logs", []),
    }


if __name__ == "__main__":

    question = input("Ask your database: ")
    response = run_agent(question)

    print("\nSTATUS:", response["status"])
    print("\nGENERATED SQL:")
    print(response["generated_sql"])

    print("\nRESULTS:")
    for row in response["results"]:
        print(row)

    print("\nEXECUTION LOGS:")
    for log in response["logs"]:
        print("-", log)
