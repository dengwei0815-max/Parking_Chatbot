import pytest
from rag import ask_chatbot

def test_info_retrieval():
    response = ask_chatbot("What are the parking prices?")
    # Accept "rate" or "$2" as valid answers
    assert any(keyword in response.lower() for keyword in ["price", "rate", "$2"])

def test_reservation_flow():
    response = ask_chatbot("I want to reserve a parking space.")
    assert "reservation" in response.lower()