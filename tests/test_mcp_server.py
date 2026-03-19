import pytest
import mcp_server
from mcp_server import process_reservation_file


class DummyReservation:
    def __init__(self, name, car_number, period):
        self.name = name
        self.car_number = car_number
        self.period = period


def test_process_reservation_file_success(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "RESERVATION_FILE", str(tmp_path / "res.txt"))
    reservation = DummyReservation("Test", "1234", "1 day")
    result = process_reservation_file(reservation)
    assert result is True
    content = (tmp_path / "res.txt").read_text()
    assert content.startswith("Test | 1234 | 1 day")


def test_process_reservation_file_failure(monkeypatch):
    monkeypatch.setattr(mcp_server, "RESERVATION_FILE", "/invalid_path/no_dir/file.txt")
    reservation = DummyReservation("Test", "1234", "1 day")
    result = process_reservation_file(reservation)
    assert result is False
