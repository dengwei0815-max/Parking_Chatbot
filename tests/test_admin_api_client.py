import pytest
import requests
from admin_api_client import send_reservation_to_admin, wait_for_admin_response

class DummyReservation:
    def __init__(self, name, car_number, period):
        self.name = name
        self.car_number = car_number
        self.period = period

def test_send_reservation_to_admin_success(monkeypatch):
    # Mock requests.post to simulate success
    class MockResponse:
        status_code = 200
        text = "Reservation received"
        def raise_for_status(self): pass
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: MockResponse())
    reservation = DummyReservation("Test", "1234", "1 day")
    res_id = send_reservation_to_admin(reservation)
    assert res_id is not None

def test_send_reservation_to_admin_failure(monkeypatch):
    # Mock requests.post to simulate failure
    def mock_post(*args, **kwargs):
        raise requests.RequestException("Network error")
    monkeypatch.setattr("requests.post", mock_post)
    reservation = DummyReservation("Test", "1234", "1 day")
    res_id = send_reservation_to_admin(reservation)
    assert res_id is None

def test_wait_for_admin_response_timeout(monkeypatch):
    # Mock requests.get to always timeout
    def mock_get(*args, **kwargs):
        raise requests.RequestException("Timeout")
    monkeypatch.setattr("requests.get", mock_get)
    res_id = "dummy"
    status = wait_for_admin_response(res_id, timeout=4)
    assert status == "timeout"