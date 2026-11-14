import logging

from ollama import Client

from app.config import (
    CONTEXT_WINDOW_TOKENS,
    MAX_OUTPUT_TOKENS,
    OLLAMA_HOST,
    OLLAMA_MODEL,
)
from app.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


class LLMService:
    """
    Responsible for communicating with the local
    Ollama model
    """

    def __init__(self, model=OLLAMA_MODEL, host=OLLAMA_HOST):

        self.model = model
        self.client = Client(host=host)
        self.context_window_tokens = CONTEXT_WINDOW_TOKENS
        self.max_output_tokens = MAX_OUTPUT_TOKENS
        self.last_usage: dict = {}

    def generate(self, messages: list[dict]) -> str:
        """Sending communication messages to
        Ollama and return  its response"""
        self.last_usage = {}

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "num_ctx": self.context_window_tokens,
                    "num_predict": self.max_output_tokens,
                },
            )

            self.last_usage = self._get_usage_metrics(response)

            content = response.message.content

            if not content or not content.strip():
                raise LLMServiceError("Ollama returned an empty response")

            return content.strip()

        except LLMServiceError:
            raise

        except Exception as error:
            logger.exception("LLM request failed")

            raise LLMServiceError(
                "Unable to generate a reponse from the LLM"
            ) from error

    def generate_stream(self, messages: list[dict]):
        """
        Generate an LLM response incrementally.

        Yields text chunks as they arrive from Ollama
        """

        self.last_usage = {}

        try:
            response_stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "num_ctx": self.context_window_tokens,
                    "num_predict": self.max_output_tokens,
                },
            )

            received_content = False

            for chunk in response_stream:
                self.last_usage = self._get_usage_metrics(chunk)
                content = chunk.message.content

                if content:
                    received_content = True
                    yield content

            if not received_content:
                raise LLMServiceError("The LLM returned an empty response.")
        except LLMServiceError:
            raise
        except Exception as error:
            logger.exception("LLM streaming request failed")

            raise LLMServiceError("Unable to stream a response from the LLM") from error

    def _get_usage_metrics(self, response) -> dict:

        def get_value(name):
            if isinstance(response, dict):
                return response.get(name)

            return getattr(response, name, None)

        return {
            "actual_prompt_tokens": get_value("prompt_eval_count"),
            "generated_tokens": get_value("eval_count"),
            "prompt_eval_duration_ns": get_value("prompt_eval_duration"),
            "eval_duration_ns": get_value("eval_duration"),
            "total_duration_ns": get_value("total_duration"),
            "load_duration_ns": get_value("load_duration"),
        }
