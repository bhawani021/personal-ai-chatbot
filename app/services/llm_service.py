import logging

from ollama import Client

from app.config import OLLAMA_HOST, OLLAMA_MODEL
from app.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

class LLMService:
    """
    Responsible for communicating with the local
    Ollama model
    """

    def __init__(
            self,
            model=OLLAMA_MODEL,
            host = OLLAMA_HOST):

        self.moel = model
        self.client = Client(host=host)

    def generate(self, messages: list[dict]) -> str:
        """Sending communication messages to
        Ollama and return  its response"""
        try:
            response = self.client.chat(
                model=self.moel,
                messages=messages,
            )

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
