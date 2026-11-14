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

CONTEXT_WINDOW_TOKENS = int(os.getenv("CONTEXT_WINDOW_TOKENS", "8192"))

MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))

CONTEXT_WARNING_PERCENT = int(os.getenv("CONTEXT_WARNING_PERCENT", "80"))

CONTEXT_SAFETY_MARGIN = int(os.getenv("CONTEXT_SAFETY_MARGIN", "256"))

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

    if CONTEXT_WINDOW_TOKENS <= 0:
        raise ConfigureError("CONTEXT_WINDOW_TOKENS must be greater than zero.")

    if MAX_OUTPUT_TOKENS <= 0:
        raise ConfigureError("MAX_OUTPUT_TOKENS must be greater than zero.")

    if CONTEXT_SAFETY_MARGIN < 0:
        raise ConfigureError("CONTEXT_SAFETY_MARGIN cannot be negative")

    if MAX_OUTPUT_TOKENS + CONTEXT_SAFETY_MARGIN >= CONTEXT_WINDOW_TOKENS:
        raise ConfigureError(
            "Output tokens and safety margin must leave room for input."
        )

    if not 1 <= CONTEXT_WARNING_PERCENT <= 100:
        raise ConfigureError("CONTEXT_WARNING_PERCENT must be between 1 and 100.")

    if LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigureError(f"Unsupported LOG_LEVEL: {LOG_LEVEL}")

    return True


def get_database_path() -> Path:
    return Path(DATABASE_PATH).expanduser()
