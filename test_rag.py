import pytest
from rag import ask_chatbot

def test_info_retrieval():
    response = ask_chatbot("What are the parking prices?")
    assert "price" in response.lower()

def test_reservation_flow():
    response = ask_chatbot("I want to reserve a parking space.")
    assert "reservation" in response.lower()