# 🚗 Parking Chatbot Project

An intelligent, modular parking chatbot system with Retrieval-Augmented Generation (RAG), human-in-the-loop approval, secure reservation processing, and full workflow orchestration.

---

## Project Stages

### **Stage 1: RAG Chatbot**
- Answers parking-related questions (location, hours, prices, availability)
- Collects reservation details interactively
- Uses Milvus vector database for retrieval
- Sensitive data guardrails (NER-based filtering)
- Automated tests and evaluation scripts

### **Stage 2: Human-in-the-Loop Admin Agent**
- Escalates reservation requests to a human administrator
- Admin reviews and approves/refuses requests via REST API and simple HTML UI
- Chatbot polls for admin decision and informs the user

### **Stage 3: MCP Server Integration**
- MCP server (FastAPI) receives confirmed reservations from the admin agent
- Securely writes reservation details to a text file
- Ensures only authorized agents can write reservations
- File format: `Name | Car Number | Reservation Period | Approval Time`

### **Stage 4: Orchestration via LangGraph or Workflow Logic**
- Orchestrates the entire pipeline: chatbot → admin agent → MCP server
- Ensures seamless, automated flow between all components
- Integration and load testing of the full workflow
- Unified documentation and deployment

---

## Architecture Diagram

```mermaid
flowchart TD
    User([User])
    Chatbot([Chatbot (RAG Agent)])
    Admin([Admin Agent<br/>(REST API + UI)])
    MCP([MCP Server<br/>(FastAPI)])
    File[(confirmed_reservations.txt)]

    User -->|Asks questions<br/>or requests reservation| Chatbot
    Chatbot -->|Escalates reservation| Admin
    Admin -->|If approved,<br/>send to MCP| MCP
    MCP -->|Write to file| File
    Admin -->|If refused,<br/>notify Chatbot| Chatbot
    Chatbot -->|Informs user| User
```

---

## Features

- RAG-based information retrieval
-
Interactive reservation flow
- Sensitive data filtering
- Human-in-the-loop approval (REST API + HTML dashboard)
- Secure, auditable reservation processing (MCP server)
- Full workflow orchestration (LangGraph or procedural)
- Modular, extensible codebase

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

### 4. Start Milvus (Docker required)

```bash
docker compose up -d
```

### 5. Ingest parking data (Stage 1)

```bash
python ingest_parking_data.py
```

---

## Stage 1: RAG Chatbot

```bash
python app.py
```
- Ask questions like "What are the parking hours?" or "Where is the parking lot?"
- To make a reservation, type "I want to reserve a parking space" and follow the prompts.
- Sensitive information (like names) will be filtered.

---

## Stage 2: Human-in-the-Loop Admin Agent

```bash
python admin_agent.py
```
- Open [http://localhost:5001/](http://localhost:5001/) in your browser to view and manage pending reservations.
- Approve or refuse reservations via the web UI.

---

## Stage 3: MCP Server Integration

```bash
python mcp_server.py
```
- Listens on port 8000 by default.
- Secured with an API key (`MCP_API_KEY` environment variable, default: `secret123`).
- Confirmed reservations are written to `confirmed_reservations.txt`.

---

## Stage 4: Orchestration (Workflow Integration)

### **A. If using LangGraph (latest stack):**

```bash
python orchestrator.py
```
- Orchestrates the full workflow: user → chatbot → admin agent → MCP server.
- Handles all transitions and context passing between components.

### **B. If using procedural orchestration (old stack):**

```bash
python orchestrator.py
```
- The orchestrator function coordinates user input, admin approval, and reservation recording in sequence.

---

## Execution Steps (All Stages)

1. **Start Milvus (if not already running):**
   ```bash
   docker compose up -d
   ```

2. **Ingest parking data:**
   ```bash
   python ingest_parking_data.py
   ```

3. **Start the MCP server:**
   ```bash
   python mcp_server.py
   ```

4. **Start the admin agent:**
   ```bash
   python admin_agent.py
   ```
   - Open [http://localhost:5001/](http://localhost:5001/) in your browser.

5. **Start the orchestrator:**
   ```bash
   python orchestrator.py
   ```
   - This will run the full workflow, either via LangGraph or procedural logic.

6. **Interact with the system:**
   - In the chatbot, type: `I want to reserve a parking space`
   - Enter reservation details when prompted.
   - Approve/refuse in the admin UI.
   - Chatbot will
     notify you of the admin’s decision.
   - If confirmed, check `confirmed_reservations.txt` for the new entry.

7. **Run automated tests:**
   ```bash
   pytest tests/
   ```

---

## Testing

- **Unit tests:** Each module/function in isolation.
- **Integration tests:** End-to-end workflow (user → admin → MCP → file).
- **Load tests:** (Optional) Use tools like Locust or pytest-benchmark.

---

## Troubleshooting

- **Milvus connection errors:** Make sure Milvus is running (`docker ps`).
- **Schema errors:** Drop and recreate the collection if you change the schema.
- **Admin agent not receiving reservations:** Check both terminals for errors, ensure both are running and using the same port.
- **MCP server not writing file:** Check for API key mismatch or file permissions.
- **Orchestrator errors:** Ensure all services are running and ports are correct.

---

## Security

- MCP server requires a valid API key in the `x-api-key` header for all write operations.
- For production, use environment variables and HTTPS.

---

## License

MIT

---

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [Milvus](https://milvus.io/)
- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [OpenAI](https://openai.com/)
- [DeepSeek](https://platform.deepseek.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)

---
