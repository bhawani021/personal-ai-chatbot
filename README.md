# Personal AI Chatbot

A command-line personal assistant built in Python, powered by a local
[Ollama](https://ollama.com/) model, with streaming responses and conversations
persisted in SQLite.

## Requirements

- Python 3.11 or newer
- Ollama installed and running locally

## Install Ollama on macOS

1. Download the [Ollama macOS app](https://ollama.com/download/mac).
2. Open the downloaded disk image, move Ollama to **Applications**, and launch
   the app. Complete its first-run setup.
3. Keep Ollama running while using this chatbot. Its local server defaults to
   `http://localhost:11434`.

Check that the command-line tool is available:

```bash
ollama --version
```

## Setup

From the repository root, create and activate a virtual environment and install
the application and development dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the example configuration and download the example model:

```bash
cp .env.example .env
ollama pull llama3.2:3b
```

You can optionally test the model directly in Ollama:

```bash
ollama run llama3.2:3b
```

### Configuration

The application loads settings from `.env`. Environment variables take
precedence over the defaults shown below.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2:latest` | Ollama model name |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `DATABASE_PATH` | `data/chatbot.db` | SQLite database file |
| `SYSTEM_PROMPT` | `You are a helpful AI assistant.` | System instructions sent to the model |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |

The example `.env` selects `llama3.2:3b`. If you change the model, pull that
model with `ollama pull <model-name>`.

## Run

With the virtual environment active and Ollama running:

```bash
python main.py
```

The CLI starts a new conversation each time it launches. Use `/list` and
`/open <id>` to return to a saved conversation.

| Command | Purpose |
|---|---|
| `/new` | Create a new conversation |
| `/list` | List saved conversations |
| `/open <id>` | Open a saved conversation |
| `/rename <title>` | Rename the active conversation |
| `/delete [id]` | Delete the active or specified conversation after confirmation |
| `/search <keyword>` | Search conversation titles and messages |
| `/history` | Show the active conversation's messages |
| `/info` | Show conversation details and message counts |
| `/help` | Show the command list |
| `/exit` | Exit the chatbot |

### Streaming responses

Chat responses are streamed to the terminal as Ollama generates them. The
completed user/assistant exchange is saved to SQLite only after the stream
finishes successfully. If generation fails, the partial response is not saved
as conversation history.

## Architecture

- `main.py` validates configuration, initializes logging and SQLite, creates
  the repository and chatbot, and runs the interactive command loop.
- `app/config.py` loads and validates the Ollama, database, prompt, and logging
  settings.
- `app/database.py` creates the SQLite schema and manages database connections.
- `app/repositories/conversation_repository.py` provides conversation and
  message persistence, search, and atomic message batches.
- `app/services/persistent_chatbot.py` manages conversation state, builds LLM
  context from stored messages, streams response chunks, and saves each
  user/assistant exchange after a complete successful response.
- `app/services/llm_service.py` sends requests to the configured Ollama model
  and yields streaming response chunks.
- `app/exceptions.py` defines application-level errors, and
  `app/logging_config.py` configures console and file logging. Logs are written
  to `logs/chatbot.log`.
- `app/chatbot.py` contains the earlier in-memory chatbot. The CLI uses
  `PersistentChatbot`; `app/services/context_manager.py` and
  `app/services/conversation_service.py` are placeholders.

## Repository structure

```text
personal-ai-chatbot/
├── app/
│   ├── chatbot.py
│   ├── config.py
│   ├── database.py
│   ├── exceptions.py
│   ├── logging_config.py
│   ├── repositories/
│   │   └── conversation_repository.py
│   └── services/
│       ├── context_manager.py       # placeholder
│       ├── conversation_service.py  # placeholder
│       ├── llm_service.py
│       └── persistent_chatbot.py
├── tests/
│   ├── run_manual.py
│   ├── test_config.py
│   ├── test_conversation_repository.py
│   ├── test_database.py
│   ├── test_llm_service.py
│   ├── test_main.py
│   └── test_persistent_chatbot.py
├── .env.example
├── main.py
├── pyproject.toml
└── requirements.txt
```

The database and log files are generated locally and ignored by Git.

## SQLite conversation storage

The database is initialized by `Database.initialize()` at the path configured
by `DATABASE_PATH`. It creates:

- `conversations` for conversation IDs, titles, system prompts, and timestamps.
- `messages` for user and assistant messages, with a foreign key that deletes
  associated messages when a conversation is deleted.

`ConversationRepository` creates, retrieves, lists, renames, deletes, and
searches conversations, and adds or retrieves their messages. Both messages in
a chat exchange are saved in one transaction after a streamed response
completes successfully. If an Ollama request fails mid-stream, any partial text
already shown in the terminal is not persisted as conversation history.

To run the repository example from the project root (it writes to the
configured database):

```bash
PYTHONPATH=. python tests/run_manual.py
```

## Tests and code quality

Run the unit tests:

```bash
python -m unittest discover -s tests -v
```

The LLM service is mocked in unit tests, including streaming behavior, so
Ollama does not need to be running to run the test suite.

Formatting, linting, and type-checking settings are in `pyproject.toml`:

```bash
ruff check app tests main.py
black --check app tests main.py
mypy app main.py
```

To measure test coverage:

```bash
coverage run -m unittest discover -s tests
coverage report
```
