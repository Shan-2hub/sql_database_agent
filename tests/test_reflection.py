
from types import SimpleNamespace

import pytest

from app.agent import nodes
from app.agent.nodes import reflection_node
from app.agent.runner import run_agent


class FakeChatModel:
    """Mock LLM that returns predefined SQL responses."""

    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    def invoke(self, prompt):
        response = self.responses[self.call_count]
        self.call_count += 1

        return SimpleNamespace(content=response)


def mock_llm(monkeypatch, responses):
    """Replace OpenAI with a deterministic mock."""

    fake_model = FakeChatModel(responses)

    monkeypatch.setattr(
        nodes,
        "ChatOpenAI",
        lambda **kwargs: fake_model
    )

    return fake_model


def test_reflection_increments_retry_count():

    state = {
        "retry_count": 0,
        "generated_sql": (
            "SELECT * FROM orders ORDER BY created_at"
        ),
        "error_message": "no such column: created_at",
        "schema_text": (
            "Table: orders\n"
            "- id: INTEGER\n"
            "- order_date: DATE"
        ),
        "user_query": "Show orders sorted by date",
        "logs": [],
    }

    result = reflection_node(state)

    assert result["retry_count"] == 1

    assert "created_at" in result["correction_feedback"]

    assert "order_date" in result["correction_feedback"]


def test_agent_recovers_from_invalid_column(monkeypatch):

    fake_model = mock_llm(
        monkeypatch,
        [
            "SELECT * FROM orders ORDER BY created_at;",
            "SELECT * FROM orders ORDER BY order_date;",
        ],
    )

    result = run_agent(
        "Show all orders sorted by date."
    )

    assert result["status"] == "success"

    assert result["retry_count"] == 1

    assert "order_date" in result["generated_sql"]

    assert result["row_count"] == 10

    assert fake_model.call_count == 2

    assert any(
        "Reflection attempt 1/3" in log
        for log in result["logs"]
    )


def test_agent_stops_after_three_retries(monkeypatch):

    fake_model = mock_llm(
        monkeypatch,
        [
            "SELECT * FROM orders ORDER BY created_at;",
            "SELECT * FROM orders ORDER BY created_at;",
            "SELECT * FROM orders ORDER BY created_at;",
            "SELECT * FROM orders ORDER BY created_at;",
        ],
    )

    result = run_agent(
        "Show all orders sorted by date."
    )

    assert result["status"] == "error"

    assert result["retry_count"] == 3

    assert fake_model.call_count == 4

    assert "created_at" in result["error"]


def test_agent_executes_valid_query_without_retry(monkeypatch):

    fake_model = mock_llm(
        monkeypatch,
        [
            "SELECT * FROM orders ORDER BY order_date;",
            "SELECT * FROM orders ORDER BY order_date;",
        ],
    )

    result = run_agent(
        "Show all orders sorted by date."
    )

    print("\nDEBUG STATUS:", result["status"])
    print("DEBUG ERROR:", result["error"])
    print("DEBUG RETRIES:", result["retry_count"])
    print("DEBUG SQL:", result["generated_sql"])
    print("DEBUG LOGS:", result["logs"])

    assert result["status"] == "success"
