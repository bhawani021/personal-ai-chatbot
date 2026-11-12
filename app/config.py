import os
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions import ConfigureError

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/chatbot.db").strip()

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful AI assistant.",
).strip()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def validate_config():
    if not OLLAMA_HOST:
        raise ConfigureError("OLLAMA_HOST cannot be empty.")

    if not OLLAMA_MODEL:
        raise ConfigureError("OLLAMA_MODEL cannot be empty.")

    if not DATABASE_PATH:
        raise ConfigureError("DATABASE_PATH cannot be empty.")

    if not SYSTEM_PROMPT:
        raise ConfigureError("SYSTEM_PROMPT cannot be empty.")

    if LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigureError(f"Unsupported LOG_LEVEL: {LOG_LEVEL}")

    return True


def get_database_path() -> Path:
    return Path(DATABASE_PATH).expanduser()
