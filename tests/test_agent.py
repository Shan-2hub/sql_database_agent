
from types import SimpleNamespace

from sqlalchemy import inspect

from app.agent import nodes
from app.agent.runner import run_agent
from app.database.connection import engine


class FakeChatModel:
    def __init__(self, sql):
        self.sql = sql

    def invoke(self, prompt):
        return SimpleNamespace(content=self.sql)


def test_agent_blocks_destructive_sql(monkeypatch):

    fake_model = FakeChatModel(
        "DROP TABLE orders;"
    )

    monkeypatch.setattr(
        nodes,
        "ChatOpenAI",
        lambda **kwargs: fake_model
    )

    result = run_agent(
        "Show all orders."
    )

    assert result["status"] == "blocked"

    assert "Only SELECT queries are permitted." in result["error"]
    # Verify that the original table still exists.
    inspector = inspect(engine)

    assert "orders" in inspector.get_table_names()


def test_agent_blocks_multiple_statements(monkeypatch):

    fake_model = FakeChatModel(
        "SELECT * FROM orders; DROP TABLE orders;"
    )

    monkeypatch.setattr(
        nodes,
        "ChatOpenAI",
        lambda **kwargs: fake_model
    )

    result = run_agent(
        "Show all orders."
    )

    assert result["status"] == "blocked"

    assert "orders" in inspect(engine).get_table_names()
