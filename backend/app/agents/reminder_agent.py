def reminder_agent(state: dict) -> dict:
    patient = state["patient"]
    risk = state["risk"]
    refill = state.get("refill", {})

    medication = patient["medication"]

    if refill.get("refill_status") == "overdue":
        message = (
            f"Hi, this is a reminder that your {medication} refill may be overdue. "
            "Please check with your pharmacy or care team."
        )
    else:
        message = (
            f"Hi, this is a friendly reminder to take your {medication} as prescribed."
        )

    return {
        "reminder": {
            "channel": patient["preferred_contact"],
            "message": message,
            "risk_level": risk["risk_level"],
        }
    }