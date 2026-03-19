# Parking Chatbot Project

An intelligent, modular parking chatbot system with Retrieval-Augmented Generation (RAG), a LangChain admin agent with human-in-the-loop approval, secure reservation recording, LangGraph workflow orchestration, and guardrails that protect sensitive data in both directions.

---

## Architecture Overview

```
User (CLI)
   │
   ▼
app.py  ──────────────────────────────────────────────────────────┐
   │  filter_input (guard_rails)                                   │
   │  ask_chatbot (rag.py → Milvus → Azure OpenAI)                │
   │  filter_output (guard_rails)                                  │
   │                                                               │
   │  [reservation request]                                        │
   ▼                                                               │
admin_agent.py (Flask :5001)                                       │
   │  POST /reservation  ←─── chatbot submits                     │
   │  GET  /reservation/<id>/status  ←─── chatbot polls           │
   │  POST /decision/<id>  ←─── admin clicks Confirm/Refuse       │
   │  SQLite (reservations.db)                                     │
   ▼                                                               │
mcp_server.py                                                      │
   │  process_reservation_file()  ─── writes confirmed_reservations.txt
   │  record_reservation_tool (@tool, LangChain function call)     │
   ▼                                                               │
orchestrator.py  (LangGraph StateGraph)                            │
   user_node → admin_node → mcp_node → user_node (loop)   ────────┘
        │            │
        │     admin_langchain_agent.py
        │       (LangChain AgentExecutor)
        │       Tools: get_pending_reservations
        │              decide_reservation
        ▼
confirmed_reservations.txt
reservations.db
```

---

## Project Stages

### Stage 1 — RAG Chatbot
- Answers parking questions (location, hours, rates, availability) via Milvus vector DB + Azure OpenAI
- Collects reservation details interactively
- NER-based guardrails redact person names from both user input and LLM output
- RAG chain is built once and cached (no rebuild on every call)

### Stage 2 — LangChain Admin Agent
- `admin_langchain_agent.py` is a real LangChain `AgentExecutor` using `create_tool_calling_agent`
- Two tools: `get_pending_reservations` (read from SQLite) and `decide_reservation` (write decision to SQLite)
- `admin_agent.py` provides a Flask web dashboard for human-in-the-loop approval
  - Session-based authentication (password via `ADMIN_PASSWORD` env var)
  - All reservations persisted in SQLite — no data loss on restart
  - Jinja2 auto-escaping throughout — no XSS risk

### Stage 3 — MCP / Reservation Recording (tool/function-call fallback)
- `mcp_server.py` exposes reservation recording as a **LangChain `@tool`** (`record_reservation_tool`) — satisfies the task's "use tool/function call for writing data into file" requirement
- `process_reservation_file()` is the plain-Python equivalent used by `orchestrator.mcp_node`
- Both write to `confirmed_reservations.txt` with a timestamp in the format: `Name | Car | Period | Time`

### Stage 4 — LangGraph Orchestration
- `orchestrator.py` uses `langgraph.graph.StateGraph` with a typed `WorkflowState` (`TypedDict`)
- Three explicit workflow nodes:
  - `user_node` — user interaction, RAG chatbot, guardrails
  - `admin_node` — LangChain agent drives approval decision
  - `mcp_node` — records confirmed reservations via MCP tool
- Conditional routing between nodes via `add_conditional_edges`

---

## Project Structure

```
parking-chatbot/
├── app.py                    # Chatbot CLI entry point
├── orchestrator.py           # LangGraph workflow (user → admin → mcp)
├── rag.py                    # RAG chain (cached singleton)
├── guard_rails.py            # NER-based input/output redaction
├── admin_agent.py            # Flask admin dashboard + chatbot REST API
├── admin_langchain_agent.py  # LangChain AgentExecutor (second agent)
├── admin_api_client.py       # Chatbot-side HTTP client for admin polling
├── mcp_server.py             # LangChain @tool + plain function for reservation recording
├── reservation.py            # Reservation data model
├── reservation_db.py         # SQLite helpers (init, save, get, get_all)
├── ingest_parking_data.py    # One-time Milvus data ingestion
├── db.py                     # Milvus collection schema helpers
├── evaluation.py             # Latency + semantic similarity evaluation
├── run_evaluation.py         # Evaluation entry point (writes evaluation_report.txt)
├── docker-compose.yml        # Milvus stack (etcd, minio, standalone)
├── requirements.txt
├── volumes/
│   └── var.py                # Azure OpenAI env var loading
└── tests/
    ├── test_e2e.py            # End-to-end tests (7 scenarios, 24 tests)
    ├── test_integration.py    # Integration tests (nodes, DB, Flask, caching)
    ├── test_guard_rails.py    # Guard-rails unit tests
    ├── test_mcp_server.py     # MCP file-write tests
    ├── test_admin_api_client.py
    └── test_rag.py            # RAG tests (requires live Milvus + OpenAI)
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/parking-chatbot.git
cd parking-chatbot
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file or export these in your shell:

```bash
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=...
export AZURE_OPENAI_DEPLOYMENT_NAME=...
export AZURE_OPENAI_API_VERSION=...
export ADMIN_PASSWORD=adminpass          # admin dashboard password
export FLASK_SECRET_KEY=change-me       # Flask session secret
```

### 5. Start Milvus (Docker required)

```bash
docker compose up -d
```

Wait ~30 seconds, then verify:

```bash
docker ps   # etcd, minio, milvus-standalone should all show Up
```

### 6. Ingest parking data (run once)

```bash
python ingest_parking_data.py
```

Expected output: `Data ingestion complete!`

---

## Running the System

Open **two terminals**.

**Terminal 1 — Admin dashboard:**

```bash
python admin_agent.py
```

Open `http://localhost:5001` in your browser and log in with `ADMIN_PASSWORD`.

**Terminal 2 — Chatbot (app.py direct) or full LangGraph workflow:**

```bash
# Simple chatbot + REST polling flow
python app.py

# Full LangGraph orchestrated flow (user_node → admin_node → mcp_node)
python orchestrator.py
```

### Example interaction

```
You: What are the parking hours?
Bot: The parking lot is open 24 hours a day.

You: I want to reserve a parking space
Please enter your name: Alice Smith
Please enter your car number: AB-1234
Please enter reservation period: 2 days
Waiting for admin approval...
```

In the browser at `http://localhost:5001`, click **Confirm**.

```
Bot: Your reservation is confirmed!
```

Check the output file:

```bash
cat confirmed_reservations.txt
# Alice Smith | AB-1234 | 2 days | 2026-03-19 14:32:01
```

---

## Guardrails

Sensitive data (person names) is protected in both directions:

| Direction | Function | Effect |
|---|---|---|
| User input → LLM | `filter_input()` | Detected names replaced with `[REDACTED]` before reaching vector DB / LLM |
| LLM output → User | `filter_output()` | Detected names replaced with `[REDACTED]` before display |

The NER model (`dbmdz/bert-large-cased-finetuned-conll03-english`) is loaded once at import time. Redaction does not block the conversation — the message continues with names masked.

---

## Testing

### Run all offline tests (no LLM or Milvus needed)

```bash
pytest tests/test_e2e.py tests/test_integration.py tests/test_guard_rails.py tests/test_mcp_server.py tests/test_admin_api_client.py -v
```

### Run only end-to-end tests

```bash
pytest tests/test_e2e.py -v
```

End-to-end test scenarios:

| Scenario | Description |
|---|---|
| E2E-1 RAG query | User question → chatbot answers, LLM output redacted |
| E2E-2 Confirmed reservation | Full user→admin→mcp flow, admin confirms, file written |
| E2E-3 Refused reservation | Full flow, admin refuses, file not written |
| E2E-4 Admin dashboard | Auth, POST/GET reservation, confirm/refuse via web UI, edge cases |
| E2E-5 Guardrails | Name in input redacted before LLM; name in output redacted before display |
| E2E-6 Persistence | Reservation survives new DB connection; bulk storage |
| E2E-7 Concurrency | 10 simultaneous chatbot POSTs all stored without collision |

### Run RAG tests (requires live Milvus + Azure OpenAI)

```bash
pytest tests/test_rag.py -v
```

### Run evaluation report

```bash
python run_evaluation.py
```

Outputs average latency and semantic similarity scores, writes `evaluation_report.txt`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Collection 'parking_info' not found` | Run `python ingest_parking_data.py` |
| `Connection refused :19530` | Run `docker compose up -d` and wait for Milvus to be healthy |
| `AuthenticationError` from Azure OpenAI | Check env vars are exported in the same shell |
| `Invalid password` on admin dashboard | Check `ADMIN_PASSWORD` env var matches what you type |
| `confirmed_reservations.txt` not created | Check file permissions; admin must approve first |
| `pytest ImportError` on LangChain | Run `pip install -r requirements.txt` inside the venv |

---

## Security Notes

- Admin dashboard requires session login; password is read from `ADMIN_PASSWORD` env var
- All Jinja2 templates use `{{ }}` auto-escaping — no `|safe` on user-supplied data
- NER guardrails redact names from both user input and LLM output
- For production: use HTTPS, rotate `FLASK_SECRET_KEY`, and store credentials in a secrets manager

---

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Milvus](https://milvus.io/)
- [HuggingFace Transformers](https://huggingface.co/)
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

---

## License

MIT
