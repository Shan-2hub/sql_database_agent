import sqlglot
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import inspect, text

from app.database.connection import engine
from app.agent.prompts import SQL_GENERATION_PROMPT
from app.security.sql_validator import (
    validate_sql,
    SQLSecurityError,
)


load_dotenv()


def inspect_schema_node(state):
    """Inspect database tables and columns."""

    inspector = inspect(engine)
    schema_info = {}

    for table_name in inspector.get_table_names():
        schema_info[table_name] = [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
            }
            for column in inspector.get_columns(table_name)
        ]

    schema_text = ""

    for table_name, columns in schema_info.items():
        schema_text += f"\nTable: {table_name}\n"

        for column in columns:
            schema_text += (
                f"- {column['name']}: {column['type']}\n"
            )

    return {
        "schema_info": schema_info,
        "schema_text": schema_text,
        "logs": state.get("logs", []) + [
            "Database schema inspected successfully."
        ],
        "status": "processing",
    }



def generate_sql_node(state):
    """Generate and normalize SQL using the OpenAI language model."""

    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0,
        timeout=30,
        max_retries=2,
    )

    prompt = SQL_GENERATION_PROMPT.format(
        schema_text=state["schema_text"],
        user_query=state["user_query"],
        correction_feedback=state.get(
            "correction_feedback", "None"
        ),
    )

    response = model.invoke(prompt)
    generated_sql = response.content

    if not isinstance(generated_sql, str):
        raise ValueError("LLM returned an unexpected response format.")

    generated_sql = generated_sql.strip()

    # Remove accidental Markdown SQL fences.
    if generated_sql.startswith("```"):
        generated_sql = generated_sql.split("\n", 1)[-1]
        generated_sql = generated_sql.rsplit("```", 1)[0].strip()

    # Normalize SQL formatting without changing query logic.
    parsed_sql = sqlglot.parse_one(
        generated_sql,
        read="sqlite",
    )
    generated_sql = parsed_sql.sql(dialect="sqlite")

    return {
        "generated_sql": generated_sql,
        "logs": state.get("logs", []) + [
            f"SQL generated: {generated_sql}"
        ],
        "error_message": "",
        "error_type": "",
    }



def validate_sql_node(state):
    """Validate generated SQL before database execution."""

    generated_sql = state["generated_sql"]

    try:
        validate_sql(generated_sql)

        return {
            "status": "validated",
            "logs": state.get("logs", []) + [
                "SQL AST validation passed."
            ],
        }

    except SQLSecurityError as error:

        return {
            "status": "blocked",
            "error_type": "security",
            "error_message": str(error),
            "logs": state.get("logs", []) + [
                f"Security validation blocked query: {error}"
            ],
        }



def execute_query_node(state):
    """Execute validated read-only SQL."""

    try:
        with engine.connect() as connection:

            if engine.dialect.name == "sqlite":
                connection.exec_driver_sql(
                    "PRAGMA query_only = ON"
                )

            try:
                result = connection.execute(
                    text(state["generated_sql"])
                )

                columns = list(result.keys())

                rows = result.fetchmany(
                    int(os.getenv("MAX_ROWS", "500"))
                )

                db_result = [
                    {
                        key: (
                            value
                            if value is None or isinstance(
                                value,
                                (str, int, float, bool)
                            )
                            else str(value)
                        )
                        for key, value in row._mapping.items()
                    }
                    for row in rows
                ]

            finally:
                if engine.dialect.name == "sqlite":
                    connection.exec_driver_sql(
                        "PRAGMA query_only = OFF"
                    )

        return {
            "db_result": db_result,
            "columns": columns,
            "row_count": len(db_result),
            "status": "success",
            "error_message": "",
            "error_type": "",
            "logs": state.get("logs", []) + [
                f"Query executed successfully. "
                f"Returned {len(db_result)} rows."
            ],
        }

    except Exception as error:

        return {
            "status": "error",
            "error_type": "database",
            "error_message": str(error),
            "logs": state.get("logs", []) + [
                f"Database execution error: {error}"
            ],
        }

def reflection_node(state):
    """Analyze database errors and prepare SQL correction."""

    retry_count = state.get("retry_count", 0) + 1

    feedback = f"""
The previous SQL query failed.

Previous SQL:
{state.get('generated_sql', '')}

Database error:
{state.get('error_message', '')}

Actual database schema:
{state.get('schema_text', '')}

Original user request:
{state.get('user_query', '')}

Analyze the error and generate a corrected SQL query.
Use only existing table and column names.
Do not change the user's original intention.
Generate only a read-only SELECT statement.
"""

    return {
        "retry_count": retry_count,
        "correction_feedback": feedback,
        "logs": state.get("logs", []) + [
            f"Reflection attempt {retry_count}/3: "
            "Analyzing the database error and preparing correction."
        ],
    }
