def risk_agent(state: dict) -> dict:
    patient = state["patient"]

    score = 0.0
    reasons = []

    if patient["last_refill_days_ago"] > patient["supply_days"]:
        score += 0.35
        reasons.append("Refill is overdue")

    if patient["missed_doses_last_30_days"] > 5:
        score += 0.35
        reasons.append("High number of missed doses in last 30 days")

    if patient["prior_non_adherence"]:
        score += 0.2
        reasons.append("Patient has prior non-adherence history")

    if patient["age"] >= 65:
        score += 0.1
        reasons.append("Patient is 65 or older")

    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"

    return {
        "risk": {
            "risk_score": round(score, 2),
            "risk_level": level,
            "reasons": reasons
        }
    }