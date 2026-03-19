"""
Admin Web Dashboard (Flask)
---------------------------
Provides a human-in-the-loop web UI for approving/refusing reservations.
- Session-based password authentication (password read from ADMIN_PASSWORD env var)
- Reservations persisted in SQLite via reservation_db
- Jinja2 auto-escaping prevents XSS (render_template_string uses {{ }} not |safe)
- Incoming reservation POST from the chatbot is stored immediately in DB
"""

import os
import uuid
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
from reservation_db import init_db, save_reservation, get_reservation, get_all_reservations

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "adminpass")

init_db()

# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid password."
    return render_template_string("""
        <h2>Admin Login</h2>
        {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
        <form method="post">
            Password: <input type="password" name="password">
            <input type="submit" value="Login">
        </form>
    """, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

DASHBOARD_TEMPLATE = """
<h2>Pending Reservations</h2>
<a href="{{ url_for('logout') }}">Logout</a>
<table border="1" cellpadding="6">
    <tr>
        <th>ID</th><th>Name</th><th>Car Number</th><th>Period</th>
        <th>Status</th><th>Action</th>
    </tr>
    {% for r in reservations %}
    <tr>
        <td>{{ r[0] }}</td>
        <td>{{ r[1] }}</td>
        <td>{{ r[2] }}</td>
        <td>{{ r[3] }}</td>
        <td>{{ r[4] }}</td>
        <td>
            {% if r[4] == 'pending' %}
            <form method="post" action="{{ url_for('admin_decision', res_id=r[0]) }}">
                <button name="decision" value="confirmed" type="submit">Confirm</button>
                <button name="decision" value="refused"   type="submit">Refuse</button>
            </form>
            {% else %}
            ({{ r[4] }})
            {% endif %}
        </td>
    </tr>
    {% else %}
    <tr><td colspan="6">No reservations.</td></tr>
    {% endfor %}
</table>
"""


@app.route("/")
@login_required
def admin_dashboard():
    reservations = get_all_reservations()
    return render_template_string(DASHBOARD_TEMPLATE, reservations=reservations)


@app.route("/decision/<res_id>", methods=["POST"])
@login_required
def admin_decision(res_id):
    decision = request.form.get("decision")
    if decision not in ("confirmed", "refused"):
        return "Invalid decision.", 400
    row = get_reservation(res_id)
    if row is None:
        return "Reservation not found.", 404
    save_reservation(row[0], row[1], row[2], row[3], decision)
    return redirect(url_for("admin_dashboard"))


# ── Chatbot-facing REST API ───────────────────────────────────────────────────

@app.route("/reservation", methods=["POST"])
def receive_reservation():
    """Called by the chatbot to submit a new reservation for admin review."""
    data = request.get_json(force=True)
    res_id    = data.get("id") or str(uuid.uuid4())
    name      = data.get("name", "")
    car_number = data.get("car_number", "")
    period    = data.get("period", "")
    if not all([name, car_number, period]):
        return jsonify({"error": "Missing fields"}), 400
    save_reservation(res_id, name, car_number, period, "pending")
    return jsonify({"id": res_id, "status": "pending"}), 201


@app.route("/reservation/<res_id>/status", methods=["GET"])
def reservation_status(res_id):
    """Called by the chatbot to poll for an admin decision."""
    row = get_reservation(res_id)
    if row is None:
        return jsonify({"error": "Not found"}), 404
    # row = (id, name, car_number, period, status)
    return jsonify({"id": row[0], "status": row[4]})


if __name__ == "__main__":
    app.run(port=5001, debug=False)
