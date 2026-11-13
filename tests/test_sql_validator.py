
import pytest

from app.security.sql_validator import (
    validate_sql,
    SQLSecurityError,
)


def test_valid_select_query():
    assert validate_sql(
        "SELECT * FROM orders"
    ) is True


def test_select_with_condition():
    assert validate_sql(
        "SELECT * FROM orders WHERE amount > 1000"
    ) is True


def test_select_with_order_by():
    assert validate_sql(
        "SELECT * FROM orders ORDER BY order_date DESC"
    ) is True


def test_union_select():
    assert validate_sql(
        "SELECT id FROM orders UNION SELECT id FROM orders"
    ) is True


@pytest.mark.parametrize(
    "query",
    [
        "DROP TABLE orders",
        "DELETE FROM orders",
        "UPDATE orders SET amount = 0",
        "INSERT INTO orders VALUES (11, 'Test')",
        "ALTER TABLE orders ADD COLUMN test TEXT",
        "CREATE TABLE test (id INT)",
        "TRUNCATE TABLE orders",
    ],
)
def test_block_write_operations(query):
    with pytest.raises(SQLSecurityError):
        validate_sql(query)


def test_block_multiple_statements():
    query = "SELECT * FROM orders; DROP TABLE orders;"

    with pytest.raises(SQLSecurityError):
        validate_sql(query)


def test_block_empty_query():
    with pytest.raises(SQLSecurityError):
        validate_sql("")


def test_block_invalid_syntax():
    with pytest.raises(SQLSecurityError):
        validate_sql("SELECT FROM WHERE")
