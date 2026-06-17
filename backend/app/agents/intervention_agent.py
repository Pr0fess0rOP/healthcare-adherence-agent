def intervention_agent(state: dict) -> dict:
    risk = state["risk"]
    patient = state["patient"]
    refill = state.get("refill", {"refill_status": "not_checked"})
    segment = state.get("segment", {"label": "General adherence monitoring"})

    risk_level = risk["risk_level"]
    refill_status = refill.get("refill_status", "not_checked")
    missed_doses = patient["missed_doses_last_30_days"]

    if risk_level == "high" and refill_status == "overdue":
        recommended_intervention = "Care coordinator follow-up with pharmacy refill support"
        confidence = 0.9
    elif risk_level == "high" and missed_doses >= 6:
        recommended_intervention = "Care coordinator phone call for missed-dose support"
        confidence = 0.86
    elif risk_level == "medium" and refill_status in ["due_soon", "overdue"]:
        recommended_intervention = "Targeted refill reminder"
        confidence = 0.78
    elif risk_level == "medium":
        recommended_intervention = "Personalized adherence reminder"
        confidence = 0.72
    else:
        recommended_intervention = "Standard reminder only"
        confidence = 0.64

    return {
        "intervention": {
            "recommended_intervention": recommended_intervention,
            "confidence": confidence,
            "based_on": {
                "risk_level": risk_level,
                "refill_status": refill_status,
                "segment": segment["label"],
            },
        }
    }