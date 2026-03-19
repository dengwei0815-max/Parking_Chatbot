"""
End-to-End Tests — Parking Chatbot
====================================
Covers three full user journeys through the system without requiring a live
LLM, Milvus instance, or Azure OpenAI credentials.

What runs for real (no mocking):
  - SQLite reservation database (reservation_db)
  - Flask admin dashboard (admin_agent)  — auth, POST /reservation, GET status, POST /decision
  - File recording (mcp_server.process_reservation_file)
  - Orchestrator nodes (user_node, admin_node, mcp_node) and LangGraph routing
  - Guard-rails redaction pipeline (guard_rails)

What is mocked:
  - ask_chatbot()        — replaces live Milvus + Azure OpenAI RAG call
  - run_admin_approval() — replaces live LangChain agent; returns a preset decision
  - NER pipeline (_ner)  — replaced with a fast deterministic function

Scenarios
---------
E2E-1  RAG query      : user asks a non-reservation question → chatbot answers, output redacted
E2E-2  Confirm flow   : user reserves → admin confirms → file written, DB updated
E2E-3  Refuse flow    : user reserves → admin refuses  → file NOT written, DB updated
E2E-4  Admin dashboard: login, view reservations, approve/refuse via web UI
E2E-5  Guardrails     : name in input is redacted; name in LLM output is redacted
E2E-6  Reservation persistence: reservation survives across two separate DB connections
"""

import sqlite3
import uuid
import pytest
import threading
import time

import reservation_db
import mcp_server
import guard_rails
import orchestrator
import admin_agent as admin_app_module


# ═══════════════════════════════════════════════════════════════════════════════
# Shared fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """
    Redirect ALL SQLite access to a fresh temp DB for every test.
    Patches reservation_db.DB_PATH so every function in the module uses it.
    """
    db_path = str(tmp_path / "e2e_test.db")
    monkeypatch.setattr(reservation_db, "DB_PATH", db_path)
    reservation_db.init_db()
    yield db_path


@pytest.fixture(autouse=True)
def isolated_reservation_file(tmp_path, monkeypatch):
    """Redirect confirmed_reservations.txt to a temp file for every test."""
    res_file = str(tmp_path / "confirmed_reservations.txt")
    monkeypatch.setattr(mcp_server, "RESERVATION_FILE", res_file)
    yield res_file


@pytest.fixture(autouse=True)
def mock_ner(monkeypatch):
    """
    Replace the heavy NER transformer with a fast deterministic stub.
    Detects 'PERSON_NAME' as a sentinel for tests that need redaction;
    all other text passes through unchanged.
    """
    def fake_ner(text):
        sentinel = "PERSON_NAME"
        idx = text.find(sentinel)
        if idx != -1:
            return [{
                "entity_group": "PER",
                "score": 0.99,
                "word": sentinel,
                "start": idx,
                "end": idx + len(sentinel),
            }]
        return []
    monkeypatch.setattr(guard_rails, "_ner", fake_ner)


@pytest.fixture()
def admin_client(monkeypatch):
    """
    Flask test client for the admin dashboard, wired to the isolated DB.
    Also patches ADMIN_PASSWORD to a known value.
    """
    monkeypatch.setattr(admin_app_module, "ADMIN_PASSWORD", "testpass")
    monkeypatch.setattr(admin_app_module, "init_db", lambda: None)  # already initialised
    admin_app_module.app.config["TESTING"] = True
    admin_app_module.app.config["SECRET_KEY"] = "e2e-test-secret"
    with admin_app_module.app.test_client() as client:
        yield client


def admin_login(client):
    """Helper: log in to the admin dashboard."""
    resp = client.post("/login", data={"password": "testpass"}, follow_redirects=True)
    assert b"Pending Reservations" in resp.data, "Admin login failed"


# ═══════════════════════════════════════════════════════════════════════════════
# E2E-1  RAG query — user asks a question, gets a (mocked) chatbot answer
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2E1RagQuery:
    def test_user_node_rag_response(self, monkeypatch, capsys):
        """
        user_node should call ask_chatbot, apply filter_output, set final_message,
        and route back to 'user' (not to admin).
        """
        monkeypatch.setattr(
            "orchestrator.ask_chatbot",
            lambda q: "Parking is open 24 hours.",
        )
        monkeypatch.setattr("orchestrator.filter_input", lambda t: t)
        monkeypatch.setattr("orchestrator.filter_output", lambda t: t)

        # Simulate one turn: user types a question, then EOF to stop the loop
        inputs = iter(["What are the parking hours?"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        state = {
            "user_input": None, "reservation": None,
            "admin_decision": None, "final_message": None,
            "error": None, "next": "user",
        }
        new_state = orchestrator.user_node(state)

        assert new_state["final_message"] == "Parking is open 24 hours."
        assert new_state["next"] == "user"
        assert new_state["reservation"] is None

        out = capsys.readouterr().out
        assert "Parking is open 24 hours." in out

    def test_rag_output_is_redacted(self, monkeypatch, capsys):
        """
        filter_output must be applied to the chatbot response: any PERSON_NAME
        in the LLM answer is replaced with [REDACTED] before the user sees it.
        """
        monkeypatch.setattr(
            "orchestrator.ask_chatbot",
            lambda q: "The last booking was made by PERSON_NAME yesterday.",
        )
        # Use real filter_output (NER is already mocked via autouse fixture)
        inputs = iter(["Who made the last booking?"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        state = {
            "user_input": None, "reservation": None,
            "admin_decision": None, "final_message": None,
            "error": None, "next": "user",
        }
        new_state = orchestrator.user_node(state)

        assert "PERSON_NAME" not in new_state["final_message"]
        assert "[REDACTED]" in new_state["final_message"]


# ═══════════════════════════════════════════════════════════════════════════════
# E2E-2  Full confirmed reservation flow
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2E2ConfirmedReservation:
    def _run_full_flow(self, monkeypatch, decision, tmp_path):
        """Drive user_node → admin_node → mcp_node with a given admin decision."""
        res_id = str(uuid.uuid4())

        # user_node: collect reservation details
        inputs = iter(["I want to reserve", "Alice", "AB-001", "3 days"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr("orchestrator.filter_input", lambda t: t)
        monkeypatch.setattr("orchestrator.filter_output", lambda t: t)
        monkeypatch.setattr("orchestrator.uuid.uuid4", lambda: res_id)

        state = {
            "user_input": None, "reservation": None,
            "admin_decision": None, "final_message": None,
            "error": None, "next": "user",
        }
        state = orchestrator.user_node(state)
        assert state["next"] == "admin"
        assert state["reservation"]["name"] == "Alice"

        # Verify pending record written to DB
        row = reservation_db.get_reservation(state["reservation"]["id"])
        assert row is not None
        assert row[4] == "pending"

        # admin_node: mock the LangChain agent decision
        monkeypatch.setattr("orchestrator.run_admin_approval", lambda rid, det: decision)
        state = orchestrator.admin_node(state)
        assert state["admin_decision"] == decision
        assert state["next"] == "mcp"

        # mcp_node: record confirmed reservation
        state = orchestrator.mcp_node(state)
        return state

    def test_confirmed_final_message(self, monkeypatch, tmp_path):
        state = self._run_full_flow(monkeypatch, "confirmed", tmp_path)
        assert state["final_message"] == "Your reservation is confirmed!"
        assert state["next"] == "user"

    def test_confirmed_writes_file(self, monkeypatch, tmp_path, isolated_reservation_file):
        self._run_full_flow(monkeypatch, "confirmed", tmp_path)
        content = open(isolated_reservation_file, encoding="utf-8").read()
        assert "Alice | AB-001 | 3 days" in content

    def test_confirmed_reservation_cleared_from_state(self, monkeypatch, tmp_path):
        state = self._run_full_flow(monkeypatch, "confirmed", tmp_path)
        assert state["reservation"] is None
        assert state["admin_decision"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# E2E-3  Full refused reservation flow
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2E3RefusedReservation:
    def _run_full_flow(self, monkeypatch):
        inputs = iter(["I want to reserve", "Bob", "XY-999", "1 week"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr("orchestrator.filter_input", lambda t: t)
        monkeypatch.setattr("orchestrator.filter_output", lambda t: t)

        state = {
            "user_input": None, "reservation": None,
            "admin_decision": None, "final_message": None,
            "error": None, "next": "user",
        }
        state = orchestrator.user_node(state)
        monkeypatch.setattr("orchestrator.run_admin_approval", lambda rid, det: "refused")
        state = orchestrator.admin_node(state)
        state = orchestrator.mcp_node(state)
        return state

    def test_refused_final_message(self, monkeypatch):
        state = self._run_full_flow(monkeypatch)
        assert state["final_message"] == "Sorry, your reservation was refused."

    def test_refused_does_not_write_file(self, monkeypatch, isolated_reservation_file):
        import os
        self._run_full_flow(monkeypatch)
        assert not os.path.exists(isolated_reservation_file) or \
               open(isolated_reservation_file).read() == ""


# ═══════════════════════════════════════════════════════════════════════════════
# E2E-4  Admin dashboard — web UI full flow
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2E4AdminDashboard:
    def test_unauthenticated_redirects_to_login(self, admin_client):
        resp = admin_client.get("/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_wrong_password_rejected(self, admin_client):
        resp = admin_client.post("/login", data={"password": "wrong"})
        assert resp.status_code == 200
        assert b"Invalid password" in resp.data

    def test_correct_password_grants_access(self, admin_client):
        admin_login(admin_client)
        resp = admin_client.get("/")
        assert resp.status_code == 200
        assert b"Pending Reservations" in resp.data

    def test_chatbot_posts_reservation_visible_in_dashboard(self, admin_client):
        """
        Chatbot POSTs a reservation → it appears in the admin dashboard.
        """
        res_id = str(uuid.uuid4())
        resp = admin_client.post("/reservation", json={
            "id": res_id, "name": "Carol", "car_number": "CC-100", "period": "2 days",
        })
        assert resp.status_code == 201

        admin_login(admin_client)
        dash = admin_client.get("/")
        assert b"Carol" in dash.data
        assert b"CC-100" in dash.data
        assert b"pending" in dash.data

    def test_admin_confirms_reservation_via_web(self, admin_client, isolated_reservation_file):
        """
        Admin clicks Confirm in the dashboard → status changes to confirmed,
        GET /reservation/<id>/status reflects the change.
        """
        res_id = str(uuid.uuid4())
        admin_client.post("/reservation", json={
            "id": res_id, "name": "Dave", "car_number": "DV-200", "period": "1 day",
        })

        admin_login(admin_client)
        resp = admin_client.post(
            f"/decision/{res_id}",
            data={"decision": "confirmed"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        # Poll endpoint should now return confirmed
        status_resp = admin_client.get(f"/reservation/{res_id}/status")
        assert status_resp.get_json()["status"] == "confirmed"

    def test_admin_refuses_reservation_via_web(self, admin_client):
        res_id = str(uuid.uuid4())
        admin_client.post("/reservation", json={
            "id": res_id, "name": "Eve", "car_number": "EV-300", "period": "5 days",
        })

        admin_login(admin_client)
        admin_client.post(
            f"/decision/{res_id}",
            data={"decision": "refused"},
            follow_redirects=True,
        )
        status_resp = admin_client.get(f"/reservation/{res_id}/status")
        assert status_resp.get_json()["status"] == "refused"

    def test_status_poll_returns_404_for_unknown_id(self, admin_client):
        resp = admin_client.get(f"/reservation/{uuid.uuid4()}/status")
        assert resp.status_code == 404

    def test_missing_fields_rejected(self, admin_client):
        resp = admin_client.post("/reservation", json={"id": "x", "name": "Only"})
        assert resp.status_code == 400

    def test_invalid_decision_rejected(self, admin_client):
        res_id = str(uuid.uuid4())
        admin_client.post("/reservation", json={
            "id": res_id, "name": "Frank", "car_number": "FR-400", "period": "1 day",
        })
        admin_login(admin_client)
        resp = admin_client.post(f"/decision/{res_id}", data={"decision": "maybe"})
        assert resp.status_code == 400

    def test_logout_clears_session(self, admin_client):
        admin_login(admin_client)
        admin_client.get("/logout")
        resp = admin_client.get("/")
        assert resp.status_code == 302


# ═══════════════════════════════════════════════════════════════════════════════
# E2E-5  Guardrails — redaction in both directions
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2E5Guardrails:
    def test_name_in_user_input_is_redacted_before_rag(self, monkeypatch, capsys):
        """
        If user input contains PERSON_NAME the guardrail redacts it before
        passing to ask_chatbot; the raw name must NOT reach the LLM.
        """
        captured_query = []
        monkeypatch.setattr(
            "orchestrator.ask_chatbot",
            lambda q: captured_query.append(q) or "Some answer.",
        )
        inputs = iter(["Is there space for PERSON_NAME?"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.setattr("orchestrator.filter_output", lambda t: t)

        state = {
            "user_input": None, "reservation": None,
            "admin_decision": None, "final_message": None,
            "error": None, "next": "user",
        }
        orchestrator.user_node(state)

        assert len(captured_query) == 1
        assert "PERSON_NAME" not in captured_query[0]
        assert "[REDACTED]" in captured_query[0]

    def test_name_in_llm_output_is_redacted(self, monkeypatch, capsys):
        """
        If the LLM response contains PERSON_NAME the guardrail redacts it
        before it is displayed and stored in final_message.
        """
        monkeypatch.setattr(
            "orchestrator.ask_chatbot",
            lambda q: "The space is reserved for PERSON_NAME.",
        )
        inputs = iter(["Who has bay 3?"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        state = {
            "user_input": None, "reservation": None,
            "admin_decision": None, "final_message": None,
            "error": None, "next": "user",
        }
        new_state = orchestrator.user_node(state)

        assert "PERSON_NAME" not in new_state["final_message"]
        assert "[REDACTED]" in new_state["final_message"]
        out = capsys.readouterr().out
        assert "PERSON_NAME" not in out

    def test_non_sensitive_input_unchanged(self, monkeypatch):
        """Text with no person names passes through filter_input unchanged."""
        from guard_rails import filter_input
        text = "What are the parking rates?"
        assert filter_input(text) == text


# ═══════════════════════════════════════════════════════════════════════════════
# E2E-6  Persistence — reservation survives process restart (new DB connection)
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2E6Persistence:
    def test_reservation_survives_reconnect(self, isolated_db):
        """
        Write a reservation, close the connection, open a fresh one — the row
        must still be there with the correct status.
        """
        res_id = str(uuid.uuid4())
        reservation_db.save_reservation(res_id, "Grace", "GR-500", "7 days", "pending")

        # Simulate new connection (e.g. after process restart)
        row = reservation_db.get_reservation(res_id)
        assert row is not None
        assert row[1] == "Grace"
        assert row[4] == "pending"

    def test_status_update_persists(self, isolated_db):
        res_id = str(uuid.uuid4())
        reservation_db.save_reservation(res_id, "Hank", "HK-600", "1 day", "pending")
        reservation_db.save_reservation(res_id, "Hank", "HK-600", "1 day", "confirmed")

        row = reservation_db.get_reservation(res_id)
        assert row[4] == "confirmed"

    def test_multiple_reservations_all_stored(self, isolated_db):
        ids = [str(uuid.uuid4()) for _ in range(5)]
        for i, rid in enumerate(ids):
            reservation_db.save_reservation(rid, f"User{i}", f"CAR-{i}", "1 day", "pending")

        all_rows = reservation_db.get_all_reservations()
        stored_ids = {r[0] for r in all_rows}
        for rid in ids:
            assert rid in stored_ids


# ═══════════════════════════════════════════════════════════════════════════════
# E2E-7  Concurrent reservation submissions
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2E7Concurrency:
    def test_concurrent_posts_all_stored(self, admin_client):
        """
        Multiple simultaneous chatbot POSTs must all be stored without collision.
        """
        ids = [str(uuid.uuid4()) for _ in range(10)]
        errors = []

        def post_reservation(res_id, idx):
            try:
                resp = admin_client.post("/reservation", json={
                    "id": res_id,
                    "name": f"User{idx}",
                    "car_number": f"CAR-{idx:03d}",
                    "period": "1 day",
                })
                if resp.status_code != 201:
                    errors.append(f"id={res_id} status={resp.status_code}")
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=post_reservation, args=(ids[i], i))
            for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent POST errors: {errors}"

        all_rows = reservation_db.get_all_reservations()
        stored_ids = {r[0] for r in all_rows}
        for rid in ids:
            assert rid in stored_ids, f"{rid} was not stored"
