import os

from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:latest"
)

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434"
)

SYSTEM_PROMPT = """
You are a helpful personal AI assistant.

Your responsibilities:
1. Provide clear and accurate answers.
2. Explain technical concepts with examples.
3. Use simple language when explaining complex topics.
4. Ask clarifying questions when necessary.
"""