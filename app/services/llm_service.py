from ollama import Client

from app.config import OLLAMA_HOST, OLLAMA_MODEL

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

        response = self.client.chat(
            model=self.moel,
            messages=messages,
        )

        content = response.message.content

        if not content:
            raise RuntimeError("Ollama returned an empty response")

        return content
