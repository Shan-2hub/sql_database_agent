
from sqlalchemy import inspect

from app.database.connection import engine


def inspect_database_schema():
    """
    Automatically inspect database tables,
    columns, and their data types.
    """

    inspector = inspect(engine)

    schema_information = {}

    table_names = inspector.get_table_names()

    for table_name in table_names:

        columns = inspector.get_columns(table_name)

        schema_information[table_name] = [
            {
                "column_name": column["name"],
                "data_type": str(column["type"]),
                "nullable": column["nullable"],
                "primary_key": column.get(
                    "primary_key", False
                ),
            }
            for column in columns
        ]

    return schema_information


def format_schema_for_llm(schema_information):
    """
    Convert inspected schema into readable
    text for the SQL generation LLM.
    """

    schema_text = ""

    for table_name, columns in schema_information.items():

        schema_text += f"\nTable: {table_name}\n"

        for column in columns:
            schema_text += (
                f"- {column['column_name']}: "
                f"{column['data_type']}\n"
            )

    return schema_text


if __name__ == "__main__":

    schema = inspect_database_schema()

    print("DATABASE SCHEMA:")
    print(format_schema_for_llm(schema))
