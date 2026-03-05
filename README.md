
# 🚗 Parking Chatbot Project

An intelligent parking chatbot system with Retrieval-Augmented Generation (RAG) and a human-in-the-loop reservation approval workflow.

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
- Maintains communication between chatbot and admin agent

---

## Features

- RAG-based information retrieval
- Interactive reservation flow
- Sensitive data filtering
- Human-in-the-loop approval (REST API + HTML dashboard)
- Modular, extensible codebase

---

## Setup

### **1. Clone the repository**

```bash
git clone https://github.com/yourusername/parking-chatbot.git
cd parking-chatbot
```

### **2. Create and activate a virtual environment**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### **3. Install dependencies**

```bash
pip install -r requirements.txt
```

### **4. Start Milvus (Docker required)**

```bash
docker compose up -d
```

### **5. Ingest parking data (Stage 1)**

```bash
python ingest_parking_data.py
```

---

## Stage 1: RAG Chatbot

### **Run the chatbot**

```bash
python app.py
```

- Ask questions like "What are the parking hours?" or "Where is the parking lot?"
- To make a reservation, type "I want to reserve a parking space" and follow the prompts.
- Sensitive information (like names) will be filtered.

### **Project Structure (Stage 1)**

```
parking_chatbot/
├── app.py                  # Main chatbot loop
├── db.py                   # Milvus DB schema and connection
├── rag.py                  # RAG chain logic
├── guard_rails.py          # Sensitive data filtering
├── ingest_parking_data.py  # Data ingestion script
├── evaluation.py           # Evaluation scripts
├── requirements.txt
├── README.md
└── tests/                  # Automated tests
```

---

## Stage 2: Human-in-the-Loop Admin Agent

### **Run the admin agent (REST API + HTML UI)**

```bash
python admin_agent.py
```

- Open [http://localhost:5001/](http://localhost:5001/) in your browser to view and manage pending reservations.

### **Reservation Approval Workflow**

1. User submits a reservation via chatbot.
2. Chatbot sends reservation details to admin REST API.
3. Admin reviews requests in the HTML dashboard and clicks "Confirm" or "Refuse".
4. Chatbot polls for admin decision and informs the user.

### **Project Structure (Stage 2 additions)**

```
parking_chatbot/
├── reservation.py          # Reservation data model
├── admin_agent.py          # REST API and HTML admin dashboard
├── app.py                  # Chatbot with human-in-the-loop integration
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
