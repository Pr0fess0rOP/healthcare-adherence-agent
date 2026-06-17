def summary_agent(state: dict) -> dict:
    patient = state["patient"]
    risk = state["risk"]
    segment = state.get("segment", {"label": "General adherence monitoring"})
    refill = state.get("refill", {"refill_status": "not_checked"})
    intervention = state.get(
        "intervention",
        {
            "recommended_intervention": "Standard reminder only",
            "confidence": 0.0,
        },
    )
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
        f"non-adherence. Segment: {segment['label']}. "
        f"Refill status is {refill.get('refill_status', 'not_checked')}. "
        f"Recommended intervention: {intervention['recommended_intervention']}. "
        f"Escalation required: {escalation.get('escalate', False)}."
    )

    return {
        "segment": segment,
        "refill": refill,
        "intervention": intervention,
        "escalation": escalation,
        "summary": summary,
    }