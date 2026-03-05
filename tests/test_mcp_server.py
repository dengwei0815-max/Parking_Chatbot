import pytest
from mcp_server import process_reservation_file

class DummyReservation:
    def __init__(self, name, car_number, period):
        self.name = name
        self.car_number = car_number
        self.period = period

def test_process_reservation_file_success(tmp_path):
    # Use a temp file for testing
    reservation = DummyReservation("Test", "1234", "1 day")
    file_path = tmp_path / "test_reservations.txt"
    # Patch open to use temp file
    import builtins
    orig_open = builtins.open
    builtins.open = lambda *args, **kwargs: orig_open(file_path, "a", encoding="utf-8")
    result = process_reservation_file(reservation)
    builtins.open = orig_open
    assert result is True
    assert file_path.read_text().startswith("Test | 1234 | 1 day")

def test_process_reservation_file_failure(monkeypatch):
    # Simulate file write error
    def mock_open(*args, **kwargs):
        raise IOError("Disk error")
    monkeypatch.setattr("builtins.open", mock_open)
    reservation = DummyReservation("Test", "1234", "1 day")
    result = process_reservation_file(reservation)
    assert result is False