"""
Integration / system tests
--------------------------
Tests the end-to-end flow without needing a live LLM or Milvus instance.
All external dependencies (RAG chain, admin agent, file I/O) are mocked.
"""

import uuid
import pytest


# ── Helpers / fixtures ────────────────────────────────────────────────────────

class DummyReservation:
    def __init__(self, name, car_number, period):
        self.name = name
        self.car_number = car_number
        self.period = period


# ── MCP tool: record_reservation_tool ────────────────────────────────────────

def test_record_reservation_tool_writes_file(tmp_path, monkeypatch):
    """record_reservation_tool should append a line to the reservation file.  """
    import mcp_server
    monkeypatch.setattr(mcp_server, "RESERVATION_FILE", str(tmp_path / "res.txt"))

    from mcp_server import record_reservation_tool
    result = record_reservation_tool.invoke({
        "name": "Alice", "car_number": "AB-123", "period": "2 days"
    })
    assert "Alice" in result
    content = (tmp_path / "res.txt").read_text()
    assert "Alice | AB-123 | 2 days" in content


def test_process_reservation_file_success(tmp_path, monkeypatch):
    import mcp_server
    monkeypatch.setattr(mcp_server, "RESERVATION_FILE", str(tmp_path / "res.txt"))

    from mcp_server import process_reservation_file
    r = DummyReservation("Bob", "XY-999", "1 week")
    assert process_reservation_file(r) is True
    assert "Bob | XY-999 | 1 week" in (tmp_path / "res.txt").read_text()


def test_process_reservation_file_failure(monkeypatch):
    """process_reservation_file returns False when file cannot be written."""
    import mcp_server
    monkeypatch.setattr(mcp_server, "RESERVATION_FILE", "/invalid_path/no_dir/file.txt")

    from mcp_server import process_reservation_file
    r = DummyReservation("Bob", "XY-999", "1 week")
    assert process_reservation_file(r) is False


# ── reservation_db ────────────────────────────────────────────────────────────

def test_reservation_db_roundtrip(tmp_path, monkeypatch):
    """save_reservation / get_reservation should persist and retrieve correctly."""
    import reservation_db
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(reservation_db, "DB_PATH", db_path)

    # Re-init with patched path
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS reservations "
        "(id TEXT PRIMARY KEY, name TEXT, car_number TEXT, period TEXT, status TEXT)"
    )
    conn.commit()
    conn.close()

    res_id = str(uuid.uuid4())
    reservation_db.save_reservation(res_id, "Carol", "ZZ-001", "3 days", "pending")
    row = reservation_db.get_reservation(res_id)
    assert row is not None
    assert row[1] == "Carol"
    assert row[4] == "pending"

    reservation_db.save_reservation(res_id, "Carol", "ZZ-001", "3 days", "confirmed")
    row = reservation_db.get_reservation(res_id)
    assert row[4] == "confirmed"


# ── guard_rails ───────────────────────────────────────────────────────────────

def test_filter_input_redacts_name(monkeypatch):
    """filter_input should redact person names detected by NER."""
    from guard_rails import filter_input

    # Mock the NER pipeline to return a detected person entity
    def mock_ner(text):
        if "Alice" in text:
            return [{"entity_group": "PER", "score": 0.99, "word": "Alice", "start": 11, "end": 16}]
        return []

    import guard_rails
    monkeypatch.setattr(guard_rails, "_ner", mock_ner)

    result = filter_input("My name is Alice and I want a spot.")
    assert "Alice" not in result
    assert "[REDACTED]" in result


def test_filter_output_redacts_name(monkeypatch):
    """filter_output should redact person names in LLM responses."""
    from guard_rails import filter_output

    def mock_ner(text):
        if "John" in text:
            return [{"entity_group": "PER", "score": 0.97, "word": "John", "start": 24, "end": 28}]
        return []

    import guard_rails
    monkeypatch.setattr(guard_rails, "_ner", mock_ner)

    result = filter_output("The last reservation was for John in bay 5.")
    assert "John" not in result
    assert "[REDACTED]" in result


def test_filter_input_passes_non_sensitive():
    """Non-name queries should pass through unchanged."""
    # Bypass NER by patching to return empty
    import guard_rails
    original = guard_rails._ner
    guard_rails._ner = lambda text: []
    try:
        from guard_rails import filter_input
        assert filter_input("What are the parking hours?") == "What are the parking hours?"
    finally:
        guard_rails._ner = original


# ── admin_agent Flask app ─────────────────────────────────────────────────────

@pytest.fixture()
def flask_client(tmp_path, monkeypatch):
    """Return a Flask test client with an isolated SQLite DB."""
    import reservation_db
    db_path = str(tmp_path / "admin_test.db")
    # Patch DB_PATH in the module AND in any already-imported references
    monkeypatch.setattr(reservation_db, "DB_PATH", db_path)

    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS reservations "
        "(id TEXT PRIMARY KEY, name TEXT, car_number TEXT, period TEXT, status TEXT)"
    )
    conn.commit()
    conn.close()

    import admin_agent
    # Patch init_db so it doesn't overwrite DB_PATH
    monkeypatch.setattr(admin_agent, "init_db", lambda: None)
    admin_agent.app.config["TESTING"] = True
    admin_agent.app.config["SECRET_KEY"] = "test"
    with admin_agent.app.test_client() as client:
        yield client


def test_admin_login_required(flask_client):
    resp = flask_client.get("/")
    assert resp.status_code == 302  # redirect to /login


def test_admin_login_wrong_password(flask_client):
    resp = flask_client.post("/login", data={"password": "wrong"})
    assert resp.status_code == 200
    assert b"Invalid password" in resp.data


def test_admin_login_correct_password(flask_client, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "adminpass")
    import admin_agent
    monkeypatch.setattr(admin_agent, "ADMIN_PASSWORD", "adminpass")
    resp = flask_client.post("/login", data={"password": "adminpass"})
    assert resp.status_code == 302


def test_receive_reservation_and_poll(flask_client):
    """POST /reservation should store it; GET /reservation/<id>/status returns pending."""
    res_id = str(uuid.uuid4())
    resp = flask_client.post("/reservation", json={
        "id": res_id, "name": "Dave", "car_number": "TT-100", "period": "1 day"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "pending"

    resp2 = flask_client.get(f"/reservation/{res_id}/status")
    assert resp2.status_code == 200
    assert resp2.get_json()["status"] == "pending"


def test_receive_reservation_missing_fields(flask_client):
    resp = flask_client.post("/reservation", json={"id": "x", "name": "Eve"})
    assert resp.status_code == 400


# ── rag.py caching ────────────────────────────────────────────────────────────

def test_rag_chain_singleton(monkeypatch):
    """get_rag_chain() should return the same object on repeated calls."""
    import rag
    rag._rag_chain = None  # reset singleton

    dummy_chain = object()
    monkeypatch.setattr(rag, "_build_rag_chain", lambda: dummy_chain)

    first  = rag.get_rag_chain()
    second = rag.get_rag_chain()
    assert first is second is dummy_chain

    rag._rag_chain = None  # cleanup


# ── orchestrator workflow nodes (unit-level) ──────────────────────────────────

def test_mcp_node_confirmed(tmp_path, monkeypatch):
    """mcp_node should call process_reservation_file when decision is confirmed."""
    import mcp_server
    monkeypatch.setattr(mcp_server, "RESERVATION_FILE", str(tmp_path / "res.txt"))

    import orchestrator
    state = {
        "user_input": None,
        "reservation": {"id": "abc", "name": "Frank", "car_number": "CC-55", "period": "1 day"},
        "admin_decision": "confirmed",
        "final_message": None,
        "error": None,
        "next": "mcp",
    }
    new_state = orchestrator.mcp_node(state)
    assert new_state["final_message"] == "Your reservation is confirmed!"
    content = (tmp_path / "res.txt").read_text()
    assert "Frank | CC-55 | 1 day" in content


def test_mcp_node_refused(monkeypatch):
    """mcp_node should not write file when decision is refused."""
    called = []

    import orchestrator
    monkeypatch.setattr(orchestrator, "process_reservation_file", lambda r: called.append(r))

    state = {
        "user_input": None,
        "reservation": {"id": "xyz", "name": "Grace", "car_number": "DD-66", "period": "2 days"},
        "admin_decision": "refused",
        "final_message": None,
        "error": None,
        "next": "mcp",
    }
    new_state = orchestrator.mcp_node(state)
    assert new_state["final_message"] == "Sorry, your reservation was refused."
    assert len(called) == 0
