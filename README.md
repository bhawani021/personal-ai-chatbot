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

| Variable       | Default                  | Description       |
|----------------|--------------------------|-------------------|
| `OLLAMA_MODEL` | `llama3.2:latest`        | Ollama model name |
| `OLLAMA_HOST`  | `http://localhost:11434` | Ollama server URL |

The example `.env` selects `llama3.2:3b`. Update the model setting and pull a
different model if needed.

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

The current chat implementation does not yet format messages as Ollama expects:
it uses `context` instead of `content` in some messages and nests conversation
turns in lists. The `/history` and `/reset` command handlers also do not match
the current history data structure. Chat requests may fail, and those commands
may raise errors until these issues are fixed.