
from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"


class InputSecurityError(Exception):
    """Raised when NeMo rejects unsafe input."""


class NeMoInputGuard:
    def __init__(self):
        config = RailsConfig.from_path(str(CONFIG_DIR))
        self.rails = LLMRails(config)

    async def validate_input(self, user_input: str):
        """Run NeMo input rails before SQL generation."""

        if not user_input or not user_input.strip():
            raise InputSecurityError("Input cannot be empty.")

        response = await self.rails.generate_async(
            messages=[
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        messages = response.get("messages", [])

        if not messages:
            raise InputSecurityError(
                "Input validation did not return a response."
            )

        result = messages[-1].get("content", "")

        # This marker must match the configured refusal
        # response in the guardrails configuration.
        if result == "UNSAFE_INPUT":
            raise InputSecurityError(
                "Potentially malicious input detected."
            )

        return result
