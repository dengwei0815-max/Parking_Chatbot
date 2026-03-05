# app.py

from reservation import Reservation
from rag import ask_chatbot
from guard_rails import filter_sensitive
import requests
import uuid
import time

def send_reservation_to_admin(reservation):
    """
    Send reservation details to the admin REST API.
    Returns a unique reservation ID.
    """
    res_id = str(uuid.uuid4())
    payload = {
        "id": res_id,
        "name": reservation.name,
        "car_number": reservation.car_number,
        "period": reservation.period
    }
    resp = requests.post("http://localhost:5001/reservation", json=payload)
    print("Admin API response:", resp.status_code, resp.text)  # <-- Add this line
    return res_id

def wait_for_admin_response(res_id, timeout=120):
    """
    Poll the admin REST API for a decision.
    Waits up to 'timeout' seconds.
    """
    for _ in range(timeout // 2):
        resp = requests.get(f"http://localhost:5001/reservation/{res_id}/status")
        if resp.status_code == 200:
            status = resp.json().get("status")
            if status in ["confirmed", "refused"]:
                return status
        time.sleep(2)
    return "timeout"

def main():
    print("Welcome to Parking Chatbot!")
    while True:
        user_input = input("You: ")
        filtered_input = filter_sensitive(user_input)
        if filtered_input.startswith("[Sensitive"):
            print(filtered_input)
            continue

        # Reservation flow: collect details
        if "reserve" in user_input.lower():
            name = input("Please enter your name: ")
            car_number = input("Please enter your car number: ")
            period = input("Please enter reservation period: ")
            reservation = Reservation(name, car_number, period)
            res_id = send_reservation_to_admin(reservation)
            print("Waiting for admin approval...")
            status = wait_for_admin_response(res_id)
            if status == "confirmed":
                print("Your reservation is confirmed!")
            elif status == "refused":
                print("Sorry, your reservation was refused.")
            else:
                print("No response from admin. Please try again later.")
        else:
            # Normal RAG chatbot response
            response = ask_chatbot(filtered_input)
            print("Bot:", response)

if __name__ == "__main__":
    main()