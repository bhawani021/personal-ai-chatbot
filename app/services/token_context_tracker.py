import math

from app.config import (
    CONTEXT_SAFETY_MARGIN,
    CONTEXT_WARNING_PERCENT,
    CONTEXT_WINDOW_TOKENS,
    MAX_OUTPUT_TOKENS,
)


class TokenContextTracker:
    """Estimate prompt token usage and check context limits."""

    def __init__(
        self,
        context_window_tokens: int = CONTEXT_WINDOW_TOKENS,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
        safety_margin: int = CONTEXT_SAFETY_MARGIN,
        warning_percent: int = CONTEXT_WARNING_PERCENT,
    ):
        if context_window_tokens <= 0:
            raise ValueError("Context window must be greater than zero.")
        if max_output_tokens <= 0:
            raise ValueError("Maximum output tokens must be greater than zero.")
        if safety_margin < 0:
            raise ValueError("Safety margin cannot be negative.")
        if max_output_tokens + safety_margin >= context_window_tokens:
            raise ValueError(
                "Output tokens and safety margin must leave room for input."
            )
        if not 1 <= warning_percent <= 100:
            raise ValueError("Warning percent must be between 1 and 100.")

        self.context_window_tokens = context_window_tokens
        self.max_output_tokens = max_output_tokens
        self.safety_margin = safety_margin
        self.warning_percent = warning_percent
        self.max_input_tokens = (
            context_window_tokens - max_output_tokens - safety_margin
        )

    @staticmethod
    def estimate_tokens(messages: list[dict]) -> int:
        """Approximate one token per 3.5 characters plus four per message."""
        total_characters = sum(
            len(str(message.get("content") or "")) for message in messages
        )
        return math.ceil(total_characters / 3.5) + len(messages) * 4

    def analyze(self, messages: list[dict]) -> dict:
        estimated_tokens = self.estimate_tokens(messages)
        usage_percent = estimated_tokens / self.max_input_tokens * 100
        remaining_tokens = max(self.max_input_tokens - estimated_tokens, 0)

        if estimated_tokens > self.max_input_tokens:
            status = "exceeded"
        elif usage_percent >= self.warning_percent:
            status = "warning"
        else:
            status = "normal"

        return {
            "estimated_prompt_tokens": estimated_tokens,
            "context_window_tokens": self.context_window_tokens,
            "max_output_tokens": self.max_output_tokens,
            "safety_margin_tokens": self.safety_margin,
            "max_input_tokens": self.max_input_tokens,
            "remaining_tokens": remaining_tokens,
            "usage_percent": round(usage_percent, 2),
            "status": status,
        }
