from dotenv import load_dotenv
import os
from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.options import RailStatus


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"

load_dotenv(BASE_DIR / ".env", override=False)

class InputSecurityError(Exception):
    """Raised when NeMo rejects or cannot validate user input."""


class NeMoInputGuard:
    def __init__(self):
        config = RailsConfig.from_path(str(CONFIG_DIR))
        self.rails = LLMRails(config)

    def validate_input(self, user_input: str) -> str:
        if not user_input or not user_input.strip():
            raise InputSecurityError("Input cannot be empty.")

        try:
            result = self.rails.check(
                messages=[
                    {
                        "role": "user",
                        "content": user_input.strip()
                    }
                ]
            )

            if result.status == RailStatus.BLOCKED:
                raise InputSecurityError(
                    "Potentially unsafe input detected."
                )

            if result.status not in (
                RailStatus.PASSED,
                RailStatus.MODIFIED
            ):
                raise InputSecurityError(
                    "Input validation returned an unknown status."
                )

            validated_input = result.content

            if not validated_input or not validated_input.strip():
                raise InputSecurityError(
                    "Input validation returned empty content."
                )

            return validated_input

        except InputSecurityError:
            raise
        except Exception as error:
            raise InputSecurityError(
                f"Input validation failed: {error}"
            ) from error
