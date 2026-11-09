# Personal AI Chatbot

A command-line personal assistant built in Python and connected to a local
[Ollama](https://ollama.com/) model.

## Requirements

- Python 3
- Ollama installed and running locally

## Install Ollama on macOS

1. Download the [Ollama macOS app](https://ollama.com/download/mac).
2. Open the downloaded disk image, move Ollama to **Applications**, and launch
   the app. Complete its first-run setup.
3. Keep Ollama running while using this chatbot. The app provides a local
   server at `http://localhost:11434`, which is the default address used by
   this project.

In Terminal, check that the command-line tool is available:

```bash
ollama --version
```

## Setup

Clone the repository, then create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the example configuration and download the configured model:

```bash
cp .env.example .env
ollama pull llama3.2:3b
```

You can optionally test the model directly in Ollama before starting the
chatbot:

```bash
ollama run llama3.2:3b
```

The `.env` file supports these settings:

| Variable        | Default                  | Description             |
|-----------------|--------------------------|-------------------------|
| `OLLAMA_MODEL`  | `llama3.2:latest`        | Ollama model name       |
| `OLLAMA_HOST`   | `http://localhost:11434` | Ollama server URL       |
| `DATABASE_PATH` | `data/chatbot.db`        | SQLite database file    |

The example `.env` selects `llama3.2:3b`. Update the model setting and pull a
different model if needed.

## Repository structure

```text
personal-ai-chatbot/
├── app/
│   ├── chatbot.py                 # earlier in-memory chatbot
│   ├── config.py
│   ├── database.py
│   ├── repositories/
│   │   └── conversation_repository.py
│   └── services/
│       ├── context_manager.py     # placeholder
│       ├── conversation_service.py # placeholder
│       ├── llm_service.py
│       └── persistent_chatbot.py
├── data/                         # generated locally; ignored by Git
│   └── chatbot.db
├── tests/
│   ├── test_conversation_repository.py
│   ├── test_persistent_chatbot.py
│   └── run_manual.py
├── .env.example
├── main.py
└── requirements.txt
```

## Architecture

- `main.py` initializes the SQLite database, repository, and persistent
  chatbot, then runs the interactive command loop.
- `app/config.py` loads Ollama and SQLite settings from `.env`.
- `app/database.py` creates the schema and manages SQLite connections.
- `app/repositories/conversation_repository.py` provides CRUD operations for
  conversations and their messages.
- `app/services/persistent_chatbot.py` loads stored history, builds the LLM
  request, and saves user/assistant messages after a successful response.
- `app/services/llm_service.py` sends chat requests to the configured Ollama
  model.
- `app/services/context_manager.py` and
  `app/services/conversation_service.py` are placeholders. `app/chatbot.py` is
  the earlier in-memory implementation; the CLI now uses `PersistentChatbot`.

## SQLite conversation storage

The SQLite database is initialized by `Database.initialize()` at the path
configured by `DATABASE_PATH`. It creates:

- `conversations` for conversation IDs, titles, system prompts, and timestamps.
- `messages` for user and assistant messages, with a foreign key that deletes
  associated messages when a conversation is deleted.

`ConversationRepository` provides operations to create, retrieve, list, rename,
and delete conversations, and to add or retrieve their messages. The database
file is local and the default `data/` directory is ignored by Git. The CLI
creates a new conversation at startup; use `/list` and `/open <id>` to return to
saved conversations.

To run the repository example from the project root:

```bash
PYTHONPATH=. python tests/run_manual.py
```

The example writes to the configured database. Run all automated tests with:

```bash
python -m unittest discover -s tests -v
```

## Run

With the virtual environment active and Ollama running:

```bash
python main.py
```

The app starts a new conversation when it launches. The interactive prompt
supports:

| Command      | Purpose                         |
|--------------|---------------------------------|
| `/new`       | Create a new conversation       |
| `/list`      | List saved conversations        |
| `/open <id>` | Open a saved conversation       |
| `/history`   | Show the active conversation    |
| `/help`      | Show the command list           |
| `/exit`      | Exit the chatbot                |

## Current limitations

Conversation orchestration currently lives in `PersistentChatbot`; the
`ConversationService` and `ContextManager` modules have not been implemented
yet. If an Ollama request fails, the current user message is not saved.