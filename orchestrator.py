"""
LangGraph Orchestrator
----------------------
Defines a three-node workflow using LangGraph's StateGraph:

  user_node  →  admin_node  →  mcp_node  →  (back to user_node or END)

Nodes
-----
- user_node   : handles user interaction, runs RAG chatbot, collects reservation
                details when the user asks to reserve.
- admin_node  : drives the LangChain admin agent to get an approve/refuse decision.
- mcp_node    : records a confirmed reservation via the MCP file-writing tool.

State
-----
WorkflowState is a TypedDict so LangGraph can properly type-check transitions.
"""

from typing import Optional, TypedDict, Literal
from langgraph.graph import StateGraph, END

from rag import ask_chatbot
from guard_rails import filter_input, filter_output
from admin_langchain_agent import run_admin_approval
from mcp_server import process_reservation_file
from reservation import Reservation
from reservation_db import init_db, save_reservation
import uuid

init_db()


# ── State schema ──────────────────────────────────────────────────────────────

class WorkflowState(TypedDict):
    user_input: Optional[str]
    reservation: Optional[dict]          # {id, name, car_number, period}
    admin_decision: Optional[str]        # "confirmed" | "refused"
    final_message: Optional[str]
    error: Optional[str]
    next: Optional[str]                  # routing hint


# ── Node: user interaction ────────────────────────────────────────────────────

def user_node(state: WorkflowState) -> WorkflowState:
    """
    Collect user input, apply guardrails, run RAG chatbot or start reservation flow.
    """
    try:
        raw_input = input("You: ").strip()
        filtered = filter_input(raw_input)

        if "reserve" in raw_input.lower():
            name       = input("Please enter your name: ").strip()
            car_number = input("Please enter your car number: ").strip()
            period     = input("Please enter reservation period: ").strip()
            res_id     = str(uuid.uuid4())
            # Persist as pending immediately
            save_reservation(res_id, name, car_number, period, "pending")
            return {
                **state,
                "user_input": filtered,
                "reservation": {"id": res_id, "name": name,
                                "car_number": car_number, "period": period},
                "next": "admin",
            }
        else:
            raw_response = ask_chatbot(filtered)
            response     = filter_output(raw_response)
            print("Bot:", response)
            return {
                **state,
                "user_input": filtered,
                "reservation": None,
                "final_message": response,
                "next": "user",
            }
    except (KeyboardInterrupt, EOFError):
        return {**state, "next": END}
    except Exception as e:
        print(f"[user_node error] {e}")
        return {**state, "error": str(e), "next": "user"}


# ── Node: administrator approval ──────────────────────────────────────────────

def admin_node(state: WorkflowState) -> WorkflowState:
    """
    Use the LangChain admin agent to obtain an approve/refuse decision.
    """
    try:
        res = state["reservation"]
        details_str = (
            f"Name: {res['name']}, Car: {res['car_number']}, Period: {res['period']}"
        )
        decision = run_admin_approval(res["id"], details_str)
        return {**state, "admin_decision": decision, "next": "mcp"}
    except Exception as e:
        print(f"[admin_node error] {e}")
        return {**state, "admin_decision": "refused", "error": str(e), "next": "mcp"}


# ── Node: data recording (MCP / file write) ───────────────────────────────────

def mcp_node(state: WorkflowState) -> WorkflowState:
    """
    Write confirmed reservations to the persistent store via the MCP tool.
    """
    try:
        res = state["reservation"]
        if state.get("admin_decision") == "confirmed":
            reservation_obj = Reservation(res["name"], res["car_number"], res["period"])
            process_reservation_file(reservation_obj)
            msg = "Your reservation is confirmed!"
        else:
            msg = "Sorry, your reservation was refused."
        print("Bot:", msg)
        return {
            **state,
            "final_message": msg,
            "reservation": None,
            "admin_decision": None,
            "next": "user",
        }
    except Exception as e:
        print(f"[mcp_node error] {e}")
        return {**state, "error": str(e), "next": "user"}


# ── Routing ───────────────────────────────────────────────────────────────────

def route(state: WorkflowState) -> Literal["user", "admin", "mcp", "__end__"]:
    return state.get("next", "user") or "user"


# ── Build graph ───────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("user",  user_node)
    graph.add_node("admin", admin_node)
    graph.add_node("mcp",   mcp_node)

    graph.set_entry_point("user")

    graph.add_conditional_edges("user",  route, {"user": "user", "admin": "admin", "__end__": END})
    graph.add_conditional_edges("admin", route, {"mcp": "mcp"})
    graph.add_conditional_edges("mcp",   route, {"user": "user", "__end__": END})

    return graph.compile()


# ── Entry point ───────────────────────────────────────────────────────────────

def run_workflow():
    app = build_graph()
    initial_state: WorkflowState = {
        "user_input":     None,
        "reservation":    None,
        "admin_decision": None,
        "final_message":  None,
        "error":          None,
        "next":           "user",
    }
    print("Welcome to Parking Chatbot! (type Ctrl-C to exit)")
    try:
        app.invoke(initial_state)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    run_workflow()
