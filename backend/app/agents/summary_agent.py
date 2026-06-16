def summary_agent(state: dict) -> dict:
    patient = state["patient"]
    risk = state["risk"]
    refill = state["refill"]
    escalation = state["escalation"]

    summary = (
        f"Patient {patient['patient_id']} is at {risk['risk_level']} risk for medication "
        f"non-adherence. Refill status is {refill['refill_status']}. "
        f"Escalation required: {escalation['escalate']}."
    )

    return {"summary": summary}