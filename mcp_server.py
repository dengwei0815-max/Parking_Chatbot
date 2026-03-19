"""
Reservation Recording — Tool/Function-Call Interface
------------------------------------------------------
Implements the "fallback" approach specified by the task:
  "use tool/function call for writing data into file"

Exposes two interfaces:
1. `record_reservation_tool` — a LangChain @tool used directly by the
   orchestrator and the admin LangChain agent via function-calling.
2. `process_reservation_file(reservation)` — a plain Python function used
   by orchestrator.mcp_node when the decision comes from the web dashboard.

Both write to confirmed_reservations.txt in the format:
  Name | Car Number | Period | Approval Time
"""

import os
from datetime import datetime
from langchain_core.tools import tool

RESERVATION_FILE = os.environ.get("RESERVATION_FILE", "confirmed_reservations.txt")


# ── Shared write implementation ───────────────────────────────────────────────

def _write_entry(name: str, car_number: str, period: str) -> str:
    """Append one reservation line to the file. Returns the written entry."""
    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{name} | {car_number} | {period} | {approval_time}\n"
    with open(RESERVATION_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    return entry


# ── LangChain @tool (function-call interface) ─────────────────────────────────

@tool
def record_reservation_tool(name: str, car_number: str, period: str) -> str:
    """
    Record a confirmed parking reservation to the persistent file store.

    Use this tool after a reservation has been approved to persist the record.

    Args:
        name:       Full name of the person making the reservation.
        car_number: Vehicle registration number.
        period:     Reservation period (e.g. '2 days', '1 week').

    Returns:
        Confirmation string with the recorded entry.
    """
    try:
        entry = _write_entry(name, car_number, period)
        return f"Reservation recorded: {entry.strip()}"
    except Exception as e:
        return f"Failed to record reservation: {e}"


# ── Plain function used by orchestrator.mcp_node ──────────────────────────────

def process_reservation_file(reservation) -> bool:
    """
    Write a confirmed reservation object to file.

    Args:
        reservation: object with .name, .car_number, .period attributes.

    Returns:
        True on success, False on failure.
    """
    try:
        _write_entry(reservation.name, reservation.car_number, reservation.period)
        print("Reservation written to file.")
        return True
    except Exception as e:
        print(f"Error writing reservation to file: {e}")
        return False
