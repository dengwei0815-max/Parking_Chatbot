import requests
import uuid
import time

def send_reservation_to_admin(reservation):
    """
    Send reservation details to the admin REST API.
    Returns a unique reservation ID.
    Handles network errors gracefully.
    """
    res_id = str(uuid.uuid4())
    payload = {
        "id": res_id,
        "name": reservation.name,
        "car_number": reservation.car_number,
        "period": reservation.period
    }
    try:
        resp = requests.post("http://localhost:5001/reservation", json=payload, timeout=5)
        resp.raise_for_status()
        print("Admin API response:", resp.status_code, resp.text)
        return res_id
    except requests.RequestException as e:
        print(f"Error sending reservation to admin: {e}")
        return None

def wait_for_admin_response(res_id, timeout=120):
    """
    Poll the admin REST API for a decision.
    Waits up to 'timeout' seconds.
    Handles network errors and timeouts.
    """
    if not res_id:
        print("No reservation ID provided.")
        return "error"
    for _ in range(timeout // 2):
        try:
            resp = requests.get(f"http://localhost:5001/reservation/{res_id}/status", timeout=5)
            if resp.status_code == 200:
                status = resp.json().get("status")
                if status in ["confirmed", "refused"]:
                    return status
            elif resp.status_code == 404:
                print("Reservation not found in admin agent.")
                return "error"
        except requests.RequestException as e:
            print(f"Error polling admin agent: {e}")
        time.sleep(2)
    print("Admin response timed out.")
    return "timeout"