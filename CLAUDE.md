# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Educational examples for building chatbots and AI agents with LLMs, organized as independent modules demonstrating progressive complexity: direct API usage → LangChain framework → full-stack apps → agentic loops.

## Running Code

All modules are standalone Python scripts. Run them directly:

```bash
python backend_api/test_chat_simple.py
python backend_langchain/test_05_rag.py
python ai_agent/test_loop_agent.py
python embedding_test/run_embedding_search.py
```

**Required environment variables** (`.env` file):
- `OPENAI_API_KEY` (for `backend_api/`, `backend_langchain/`, `fullstack_flask/`)
- `ANTHROPIC_API_KEY` (for `ai_agent/`)
- `PINECONE_API_KEY` (for Pinecone examples)
- `TAVILY_API_KEY` (for `ai_agent/test_chat_with_rag.py`)

### fullstack_flask app

```bash
pip install -r fullstack_flask/requirements.txt

# Initialize DB (first time only)
python -c "from src.app import app, db; app.app_context().__enter__(); db.create_all()"

gunicorn src.app:app        # http://localhost:50505
docker-compose up           # alternatively
```

### notebook_app_by_cc

```bash
# Backend (Django) — http://localhost:8000
cd notebook_app_by_cc/backend
pip install -r requirements.txt
python manage.py migrate        # first time only
python manage.py runserver

# Frontend (React + Vite) — http://localhost:5173
cd notebook_app_by_cc/frontend
npm install
npm run dev
```

Start the backend first; Vite proxies `/api/*` to `localhost:8000`. See `notebook_app_by_cc/CLAUDE.md` for full architecture details.

### fullstack_flask_minimal

```bash
flask --app src.app run     # http://0.0.0.0:5000
```

## Architecture

### Module Overview

| Module | Purpose |
|---|---|
| `embedding_test/` | GloVe word embeddings + cosine similarity, no API required |
| `backend_api/` | OpenAI SDK examples (simple → streaming → multi-turn → function calling → agents) |
| `backend_langchain/` | LangChain equivalents (prompts, memory, RAG, tool-calling agents) |
| `fullstack_flask/` | Production-style Flask app with RAG, streaming, DB persistence |
| `fullstack_flask_minimal/` | Minimal Flask starter template |
| `ai_agent/` | Agentic loops with tool execution and context window visualization (Anthropic SDK, `claude-sonnet-4-6`) |
| `notebook_app_by_cc/` | Full-stack notebook app: Django REST Framework backend + React 19 SPA frontend with JWT auth and rich text editing |

### Agentic Loop Pattern (`ai_agent/`)

`test_simple_agent.py` defines tools in Anthropic format (`name` / `input_schema`) and `execute_function_call` (accesses `tool_call.name` and `tool_call.input`). `test_loop_agent.py` imports them and runs the loop:

```
system = "..."   # passed as system= param, not in messages
messages = [{"role": "user", "content": user_message}]

while iteration < max_iterations:
    response = client.messages.create(model=..., system=system, messages=messages, tools=tools)
    tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

    if tool_use_blocks:
        messages.append({"role": "assistant", "content": response.content})
        tool_results = [{"type": "tool_result", "tool_use_id": b.id, "content": execute(b)} for b in tool_use_blocks]
        messages.append({"role": "user", "content": tool_results})
        continue
    else:
        print(text_blocks[0].text)
        break
```

Key Anthropic differences vs OpenAI:
- `system` is a top-level param, not a message role
- Tool results go back as a `user` message with `type: tool_result` content blocks
- `response.content` is a list of `TextBlock` / `ToolUseBlock` objects; access `.text`, `.name`, `.input`, `.id`
- Tool definitions use `input_schema` instead of `parameters`

Context window state is printed each iteration with ANSI colors, starting with `[function_call_definitions]` followed by the message history — matching how the model provider injects tool definitions before the conversation messages.

### RAG Pattern (`backend_langchain/`, `fullstack_flask/`)

LangChain RAG chain composition: `retriever | prompt | llm | StrOutputParser`. Vector stores used: FAISS (local), Pinecone (cloud). `fullstack_flask/src/chat_langchain.py` combines Pinecone retrieval with `ConversationBufferMemory` for persistent multi-turn RAG.

### Streaming (`fullstack_flask/`)

Flask streams NDJSON (newline-delimited JSON) via `Response(generator, mimetype="text/plain")`. Frontend consumes it with the browser `ReadableStream` API for token-by-token display.

### Database (`fullstack_flask/`)

SQLAlchemy models: `User`, `ChatMessage`. Defaults to SQLite in dev; switches to MySQL when `MYSQL_URI` env var is set (configured in `src/app.py`).
