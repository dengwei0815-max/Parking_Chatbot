

# 🚦 Execution Steps

## **1. Prepare the Environment**

- Open a terminal (PowerShell, CMD, or bash).
- Navigate to your project directory.

### **A. Create and activate a virtual environment**

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### **B. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## **2. Start Milvus (Vector Database)**

- Make sure Docker is running.
- In your project directory, start Milvus:

```bash
docker compose up -d
```

---

## **3. Ingest Parking Data (Stage 1)**

```bash
python ingest_parking_data.py
```
- This will populate Milvus with parking information for retrieval.

---

## **4. Start the MCP Server (Stage 3)**

```bash
python mcp_server.py
```
- This will start the FastAPI server on port 8000.
- (Optional) Set the API key for security:
  ```bash
  # Windows PowerShell
  $env:MCP_API_KEY="your_secret_key"
  # macOS/Linux
  export MCP_API_KEY="your_secret_key"
  ```

---

## **5. Start the Admin Agent (Stage 2)**

Open a **new terminal** (keep MCP server running):

```bash
python admin_agent.py
```
- This will start the Flask server on port 5001.
- Open [http://localhost:5001/](http://localhost:5001/) in your browser to view/manage reservations.

---

## **6. Start the Chatbot (Stage 1 & 2)**

Open another **new terminal**:

```bash
python app.py
```
- You’ll see: `Welcome to Parking Chatbot!`

---

## **7. Test the Full Workflow**

1. **In the chatbot**, type:  
   `I want to reserve a parking space`
2. **Follow the prompts** (enter name, car number, period).
3. **Chatbot will say:** `Waiting for admin approval...`
4. **Go to the admin UI** ([http://localhost:5001/](http://localhost:5001/)), find the pending reservation, and click **Confirm** or **Refuse**.
5. **Chatbot will notify you** of the admin’s decision.
6. **If confirmed**, check `confirmed_reservations.txt` (in your project folder) for the new entry.

---

## **8. Run Automated Tests (Optional)**

```bash
pytest tests/
```

---

## **Summary Table**

| Step | Command / Action                              | Result                                      |
|------|----------------------------------------------|---------------------------------------------|
| 1    | Create/activate venv, install requirements   | Python environment ready                    |
| 2    | `docker compose up -d`                       | Milvus running                              |
| 3    | `python ingest_parking_data.py`              | Data loaded into Milvus                     |
| 4    | `python mcp_server.py`                       | MCP server running on port 8000             |
| 5    | `python admin_agent.py`                      | Admin UI at http://localhost:5001/          |
| 6    | `python app.py`                              | Chatbot running                             |
| 7    | Use chatbot & admin UI                       | End-to-end reservation flow                 |
| 8    | `pytest tests/`                              | Run automated tests                         |

---

**If you encounter any errors at any step, paste the error message here and I’ll help you debug!**

If you want a one-page quickstart or a script to launch all services, let me know!