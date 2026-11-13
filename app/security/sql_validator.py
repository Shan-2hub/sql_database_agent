
import sqlglot
from sqlglot import exp


class SQLSecurityError(Exception):
    """Raised when an SQL query violates security rules."""


# SQL operations that are never permitted.
BLOCKED_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Merge,
    exp.Command,
)


def validate_sql(sql_query: str) -> bool:
    """
    Validate SQL using AST parsing.

    Only single, read-only SELECT queries are allowed.
    """

    if not sql_query or not sql_query.strip():
        raise SQLSecurityError("SQL query cannot be empty.")

    try:
        statements = sqlglot.parse(
            sql_query,
            read="sqlite"
        )
    except sqlglot.errors.ParseError as exc:
        raise SQLSecurityError(
            f"Invalid SQL syntax: {exc}"
        ) from exc

    # Reject empty queries and multiple statements.
    if len(statements) != 1 or statements[0] is None:
        raise SQLSecurityError(
            "Only one SQL statement is permitted."
        )

    tree = statements[0]

    # Root must be a SELECT query or a read-only query
    # expression such as UNION.
    if not isinstance(tree, exp.Query):
        raise SQLSecurityError(
            "Only SELECT queries are permitted."
        )

    # Inspect the complete AST, including nested expressions.
    for node in tree.walk():

        if isinstance(node, BLOCKED_EXPRESSIONS):
            raise SQLSecurityError(
                f"Blocked SQL operation: {type(node).__name__}"
            )

    return True


if __name__ == "__main__":

    test_queries = [
        "SELECT * FROM orders",
        "SELECT * FROM orders WHERE amount > 1000",
        "DROP TABLE orders",
        "DELETE FROM orders",
        "UPDATE orders SET amount = 0",
        "SELECT * FROM orders; DROP TABLE orders;",
    ]

    for query in test_queries:

        try:
            validate_sql(query)
            print(f"[ALLOWED] {query}")

        except SQLSecurityError as error:
            print(f"[BLOCKED] {query}")
            print(f"Reason: {error}")
