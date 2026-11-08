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
│   ├── chatbot.py
│   ├── config.py
│   ├── database.py
│   ├── repositories/
│   │   └── conversation_repository.py
│   └── services/
│       ├── context_manager.py
│       └── conversation_service.py
├── data/                         # generated locally; ignored by Git
│   └── chatbot.db
├── tests/
│   ├── test_conversation_repository.py
│   └── test_repository_manual.py
├── .env.example
├── main.py
└── requirements.txt
```

## Architecture

- `main.py` runs the interactive command-line loop and delegates chat requests
  to `PersonalChatbot`.
- `app/config.py` loads Ollama and SQLite settings from `.env`.
- `app/database.py` creates the SQLite schema and manages database connections.
- `app/repositories/conversation_repository.py` provides conversation and
  message persistence operations.
- `app/services/` is reserved for conversation orchestration and context
  management; these modules are currently placeholders.

The CLI still keeps its chat history in memory and does not yet call the
repository layer.

## SQLite conversation storage

The SQLite database is initialized by `Database.initialize()` at the path
configured by `DATABASE_PATH`. It creates:

- `conversations` for conversation IDs, titles, system prompts, and timestamps.
- `messages` for user and assistant messages, with a foreign key that deletes
  associated messages when a conversation is deleted.

`ConversationRepository` provides operations to create, retrieve, list, rename,
and delete conversations, and to add or retrieve their messages. The database
file is local and the default `data/` directory is ignored by Git.

To run the repository example from the project root:

```bash
PYTHONPATH=. python tests/test_repository_manual.py
```

The example writes to the configured database. Run only the automated
repository tests with:

```bash
python -m unittest discover -s tests -p 'test_conversation_repository.py' -v
```

## Run

With the virtual environment active and Ollama running:

```bash
python main.py
```

The interactive prompt lists these commands:

| Command    | Purpose                    |
|------------|----------------------------|
| `/help`    | Show the command list      |
| `/history` | Show conversation history  |
| `/reset`   | Clear conversation history |
| `/exit`    | Exit the chatbot           |

## Current limitations

The CLI does not yet use SQLite; its chat history is still kept in memory.
Conversation turns are currently stored as nested lists, which can make
follow-up Ollama requests fail. The `/history` and `/reset` command handlers do
not match the current history structure and may raise errors.