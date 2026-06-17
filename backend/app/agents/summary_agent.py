def summary_agent(state: dict) -> dict:
    patient = state["patient"]
    risk = state["risk"]
    refill = state.get("refill", {"refill_status": "not_checked"})
    escalation = state.get(
        "escalation",
        {
            "escalate": False,
            "priority": "normal",
            "reason": "Escalation was not required based on risk level",
        },
    )

    summary = (
        f"Patient {patient['patient_id']} is at {risk['risk_level']} risk for medication "
        f"non-adherence. Refill status is {refill.get('refill_status', 'not_checked')}. "
        f"Escalation required: {escalation.get('escalate', False)}."
    )

    return {
        "refill": refill,
        "escalation": escalation,
        "summary": summary,
    }