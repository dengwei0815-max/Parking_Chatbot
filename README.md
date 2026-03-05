
# 🚗 Parking Chatbot (RAG-based)

An intelligent chatbot for parking information and reservation, powered by Retrieval-Augmented Generation (RAG), LangChain, Milvus, and HuggingFace.

---

## Features

- Answers questions about parking location, hours, prices, and availability
- Handles interactive parking space reservations
- Sensitive data guardrails (NER-based filtering)
- Vector database (Milvus) for efficient retrieval
- Easily extensible and testable

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

### 5. Ingest parking data

```bash
python ingest_parking_data.py
```

### 6. Run the chatbot

```bash
python app.py
```

---

## Usage

- Type your questions (e.g., "What are the parking hours?").
- To make a reservation, follow the chatbot prompts.
- Sensitive information (like names) will be filtered.

---

## Project Structure

```
parking_chatbot/
│
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

## Configuration

- **Milvus**: Default connection is `localhost:19530`. Change in `db.py` if needed.
- **OpenAI/Azure/DeepSeek**: Set your API key as an environment variable if using LLM APIs.

---

## Testing

```bash
pytest tests/
```

---

## Troubleshooting

- **Milvus connection errors**: Make sure Milvus is running (`docker ps`).
- **Schema errors**: Drop and recreate the collection if you change the schema.
- **Missing dependencies**: Regenerate `requirements.txt` with `pip freeze > requirements.txt`.

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

