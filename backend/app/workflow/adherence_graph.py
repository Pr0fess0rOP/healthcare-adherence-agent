from typing import TypedDict, Any

from langgraph.graph import StateGraph, END

from app.agents.risk_agent import risk_agent
from app.agents.refill_agent import refill_agent
from app.agents.reminder_agent import reminder_agent
from app.agents.escalation_agent import escalation_agent
from app.agents.summary_agent import summary_agent


class AdherenceState(TypedDict, total=False):
    patient: dict[str, Any]
    risk: dict[str, Any]
    refill: dict[str, Any]
    reminder: dict[str, Any]
    escalation: dict[str, Any]
    summary: str


def route_after_risk(state: AdherenceState) -> str:
    risk_level = state["risk"]["risk_level"]

    if risk_level == "low":
        return "reminder_agent"

    return "refill_agent"


def route_after_reminder(state: AdherenceState) -> str:
    risk_level = state["risk"]["risk_level"]

    if risk_level == "high":
        return "escalation_agent"

    return "summary_agent"


def build_adherence_graph():
    graph = StateGraph(AdherenceState)

    graph.add_node("risk_agent", risk_agent)
    graph.add_node("refill_agent", refill_agent)
    graph.add_node("reminder_agent", reminder_agent)
    graph.add_node("escalation_agent", escalation_agent)
    graph.add_node("summary_agent", summary_agent)

    graph.set_entry_point("risk_agent")

    graph.add_conditional_edges(
        "risk_agent",
        route_after_risk,
        {
            "refill_agent": "refill_agent",
            "reminder_agent": "reminder_agent",
        },
    )

    graph.add_edge("refill_agent", "reminder_agent")

    graph.add_conditional_edges(
        "reminder_agent",
        route_after_reminder,
        {
            "escalation_agent": "escalation_agent",
            "summary_agent": "summary_agent",
        },
    )

    graph.add_edge("escalation_agent", "summary_agent")
    graph.add_edge("summary_agent", END)

    return graph.compile()