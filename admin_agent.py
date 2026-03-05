from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# In-memory store for demo; use a database in production
pending_reservations = {}

# MCP server config
MCP_URL = "http://localhost:8000/process_reservation"
MCP_API_KEY = os.environ.get("MCP_API_KEY", "secret123")

@app.route('/reservation', methods=['POST'])
def receive_reservation():
    """
    Receive a reservation request from the chatbot.
    """
    data = request.json
    print("Received reservation:", data)  # Debug print
    res_id = data['id']
    pending_reservations[res_id] = {'data': data, 'status': 'pending'}
    return jsonify({"message": "Reservation received", "id": res_id}), 200

@app.route('/reservation/<res_id>/status', methods=['GET'])
def get_status(res_id):
    """
    Get the current status of a reservation.
    """
    res = pending_reservations.get(res_id)
    if not res:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"status": res['status']}), 200

@app.route('/reservation/<res_id>/decision', methods=['POST'])
def admin_decision(res_id):
    """
    Admin confirms or refuses a reservation.
    If confirmed, notify MCP server.
    """
    data = request.json
    decision = data.get('decision')
    if res_id not in pending_reservations:
        return jsonify({"error": "Not found"}), 404
    if decision not in ['confirmed', 'refused']:
        return jsonify({"error": "Invalid decision"}), 400
    pending_reservations[res_id]['status'] = decision

    # Notify MCP server if confirmed
    if decision == "confirmed":
        payload = {
            "name": pending_reservations[res_id]['data']['name'],
            "car_number": pending_reservations[res_id]['data']['car_number'],
            "period": pending_reservations[res_id]['data']['period']
        }
        headers = {"x-api-key": MCP_API_KEY}
        resp = requests.post(MCP_URL, json=payload, headers=headers)
        print("MCP server response:", resp.status_code, resp.text)

    return jsonify({"message": f"Reservation {decision}"}), 200

# Simple HTML admin UI
@app.route('/')
def admin_dashboard():
    """
    HTML dashboard for admin to view and approve/refuse reservations.
    """
    html = """
    <h2>Pending Reservations</h2>
    <table border="1">
        <tr><th>ID</th><th>Name</th><th>Car Number</th><th>Period</th><th>Status</th><th>Action</th></tr>
        {% for res_id, res in reservations.items() %}
        <tr>
            <td>{{ res_id }}</td>
            <td>{{ res['data']['name'] }}</td>
            <td>{{ res['data']['car_number'] }}</td>
            <td>{{ res['data']['period'] }}</td>
            <td>{{ res['status'] }}</td>
            <td>
                {% if res['status'] == 'pending' %}
                <form method="post" action="/decision/{{ res_id }}">
                    <button name="decision" value="confirmed" type="submit">Confirm</button>
                    <button name="decision" value="refused" type="submit">Refuse</button>
                </form>
                {% else %}
                (No action)
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, reservations=pending_reservations)

@app.route('/decision/<res_id>', methods=['POST'])
def admin_decision_html(res_id):
    """
    HTML form handler for admin decision.
    """
    decision = request.form.get('decision')
    if res_id not in pending_reservations:
        return "Reservation not found", 404
    if decision not in ['confirmed', 'refused']:
        return "Invalid decision", 400
    pending_reservations[res_id]['status'] = decision

    # Notify MCP server if confirmed
    if decision == "confirmed":
        payload = {
            "name": pending_reservations[res_id]['data']['name'],
            "car_number": pending_reservations[res_id]['data']['car_number'],
            "period": pending_reservations[res_id]['data']['period']
        }
        headers = {"x-api-key": MCP_API_KEY}
        resp = requests.post(MCP_URL, json=payload, headers=headers)
        print("MCP server response:", resp.status_code, resp.text)

    return f"Reservation {res_id} {decision}. <a href='/'>Back</a>"

if __name__ == '__main__':
    app.run(port=5001)