# orchestrator.py

from app import ask_chatbot
from reservation import Reservation
from admin_api_client import send_reservation_to_admin, wait_for_admin_response
from mcp_server import process_reservation_file  # You can write a simple function for this

def orchestrate():
    print("Welcome to Parking Chatbot Orchestrator!")
    while True:
        user_input = input("You: ")
        # Stage 1: Chatbot handles user input
        response = ask_chatbot(user_input)
        print("Bot:", response)

        # Stage 2: If reservation requested, collect details and escalate
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
                # Stage 3: Write to file (MCP server simulation)
                process_reservation_file(reservation)
            elif status == "refused":
                print("Sorry, your reservation was refused.")
            else:
                print("No response from admin. Please try again later.")

if __name__ == "__main__":
    orchestrate()