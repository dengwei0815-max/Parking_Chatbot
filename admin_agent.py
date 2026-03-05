from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# In-memory store for demo; use a database in production
pending_reservations = {}

# ... (existing API routes) ...

# Simple HTML admin UI
@app.route('/')
def admin_dashboard():
    # Show all pending reservations
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
    decision = request.form.get('decision')
    if res_id not in pending_reservations:
        return "Reservation not found", 404
    if decision not in ['confirmed', 'refused']:
        return "Invalid decision", 400
    pending_reservations[res_id]['status'] = decision
    return f"Reservation {res_id} {decision}. <a href='/'>Back</a>"

@app.route('/reservation', methods=['POST'])
def receive_reservation():
    data = request.json
    print("Received reservation:", data)  # <-- Add this line
    res_id = data['id']
    pending_reservations[res_id] = {'data': data, 'status': 'pending'}
    return jsonify({"message": "Reservation received", "id": res_id}), 200
if __name__ == '__main__':
    app.run(port=5001)