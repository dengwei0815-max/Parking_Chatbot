# 🚗 Parking Chatbot Project

An intelligent, modular parking chatbot system with Retrieval-Augmented Generation (RAG), human-in-the-loop approval, and secure reservation processing.

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

---

## Features

- RAG-based information retrieval
- Interactive reservation flow
- Sensitive data filtering
- Human-in-the-loop approval (REST API + HTML dashboard)
- Secure, auditable reservation processing (MCP server)
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

### Run the chatbot

```bash
python app.py
```

- Ask questions like "What are the parking hours?" or "Where is the parking lot?"
- To make a reservation, type "I want to reserve a parking space" and follow the prompts.
- Sensitive information (like names) will be filtered.

---

## Stage 2: Human-in-the-Loop Admin Agent

### Run the admin agent (REST API + HTML UI)

```bash
python admin_agent.py
```

- Open [http://localhost:5001/](http://localhost:5001/) in your browser to view and manage pending reservations.
- Approve or refuse reservations via the web UI.

---

## Stage 3: MCP Server Integration

### Run the MCP server

```bash
python mcp_server.py
```

- Listens on port 8000 by default.
- Secured with an API key (`MCP_API_KEY` environment variable, default: `secret123`).

### How it works

1. When the admin **confirms** a reservation, the admin agent sends the reservation details to the MCP server.
2. The MCP server writes the reservation to `confirmed_reservations.txt` in the format:
   ```
   Name | Car Number | Reservation Period | Approval Time
   ```
3. Only requests with the correct API key are accepted.

### Example API call

```http
POST /process_reservation HTTP/1.1
Host: localhost:8000
x-api-key: secret123
Content-Type: application/json

{
  "
name": "David",
  "car_number": "1123",
  "period": "1 month"
}
```

---

## Project Structure

```
parking_chatbot/
├── app.py                  # Main chatbot loop
├── db.py                   # Milvus DB schema and connection
├── rag.py                  # RAG chain logic
├── guard_rails.py          # Sensitive data filtering
├── ingest_parking_data.py  # Data ingestion script
├── reservation.py          # Reservation data model
├── admin_agent.py          # REST API and HTML admin dashboard
├── mcp_server.py           # FastAPI MCP server
├── evaluation.py           # Evaluation scripts
├── requirements.txt
├── README.md
└── tests/                  # Automated tests
```

---

## Testing

```bash
pytest tests/
```

---

## Troubleshooting

- **Milvus connection errors:** Make sure Milvus is running (`docker ps`).
- **Schema errors:** Drop and recreate the collection if you change the schema.
- **Admin agent not receiving reservations:** Check both terminals for errors, ensure both are running and using the same port.
- **MCP server not writing file:** Check for API key mismatch or file permissions.

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

---
