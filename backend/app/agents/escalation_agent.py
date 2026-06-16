def escalation_agent(state: dict) -> dict:
    risk = state["risk"]
    refill = state["refill"]

    should_escalate = (
        risk["risk_level"] == "high"
        or refill["refill_status"] == "overdue"
    )

    priority = "high" if risk["risk_level"] == "high" else "normal"

    return {
        "escalation": {
            "escalate": should_escalate,
            "priority": priority,
            "reason": (
                "Patient should be reviewed by care team"
                if should_escalate
                else "No immediate escalation required"
            )
        }
    }