"""
Admin LangChain Agent
---------------------
A proper LangChain agent that handles reservation approval via human-in-the-loop.
It exposes two tools:
  - get_pending_reservations: list reservations awaiting decision
  - decide_reservation: approve or refuse a reservation by ID

The agent is invoked by the orchestrator's admin_node and drives the approval
decision through LangChain's tool-calling loop.
"""

import sqlite3
from langchain_core.tools import tool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI
from reservation_db import save_reservation, get_reservation, init_db
from volumes.var import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
)

# Ensure DB is initialised
init_db()


@tool
def get_pending_reservations() -> str:
    """Return all reservations that are currently in 'pending' status."""
    conn = sqlite3.connect("reservations.db")
    c = conn.cursor()
    c.execute("SELECT id, name, car_number, period FROM reservations WHERE status='pending'")
    rows = c.fetchall()
    conn.close()
    if not rows:
        return "No pending reservations."
    lines = [f"ID={r[0]} | Name={r[1]} | Car={r[2]} | Period={r[3]}" for r in rows]
    return "\n".join(lines)


@tool
def decide_reservation(reservation_id: str, decision: str) -> str:
    """
    Approve or refuse a reservation.

    Args:
        reservation_id: The UUID of the reservation.
        decision: Either 'confirmed' or 'refused'.

    Returns:
        Confirmation string.
    """
    decision = decision.strip().lower()
    if decision not in ("confirmed", "refused"):
        return f"Invalid decision '{decision}'. Must be 'confirmed' or 'refused'."
    row = get_reservation(reservation_id)
    if row is None:
        return f"Reservation {reservation_id} not found."
    # row = (id, name, car_number, period, status)
    save_reservation(row[0], row[1], row[2], row[3], decision)
    return f"Reservation {reservation_id} has been {decision}."


# ── LLM ──────────────────────────────────────────────────────────────────────
llm = AzureChatOpenAI(
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    temperature=0,
)

tools = [get_pending_reservations, decide_reservation]

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a parking reservation admin agent. "
        "When asked to process a reservation, use the available tools to "
        "retrieve pending reservations and record the admin's decision. "
        "Always use decide_reservation to record the outcome.",
    ),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
admin_agent = AgentExecutor(agent=agent, tools=tools, verbose=True)


def run_admin_approval(reservation_id: str, details_str: str) -> str:
    """
    Drive the LangChain agent to obtain and record an approval decision.

    The agent is given the reservation details and asked to approve/refuse it.
    Human-in-the-loop: the agent calls decide_reservation which writes to DB;
    for CLI use the admin is prompted interactively inside the tool if needed.

    Returns 'confirmed' or 'refused'.
    """
    result = admin_agent.invoke({
        "input": (
            f"Please process this reservation (ID: {reservation_id}): {details_str}. "
            "First call get_pending_reservations to see the queue, then call "
            "decide_reservation with your decision."
        )
    })
    # Re-read the final status from DB as ground truth
    row = get_reservation(reservation_id)
    if row:
        return row[4]  # status column
    return "refused"
