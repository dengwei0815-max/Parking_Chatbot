from rag import ask_chatbot
from guard_rails import filter_sensitive

def main():
    print("Welcome to Parking Chatbot!")
    while True:
        user_input = input("You: ")
        filtered_input = filter_sensitive(user_input)
        if filtered_input.startswith("[Sensitive"):
            print(filtered_input)
            continue
        response = ask_chatbot(filtered_input)
        print("Bot:", response)

if __name__ == "__main__":
    main()