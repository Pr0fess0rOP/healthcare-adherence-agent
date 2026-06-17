import os

import joblib
import pandas as pd


FEATURES = [
    "age",
    "last_refill_days_ago",
    "supply_days",
    "missed_doses_last_30_days",
    "prior_non_adherence",
]

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ml",
    "risk_model.pkl",
)

model = joblib.load(MODEL_PATH)


def build_top_factors(patient: dict) -> list[dict]:
    factors = []

    refill_delay = patient["last_refill_days_ago"] - patient["supply_days"]

    if patient["missed_doses_last_30_days"] >= 6:
        factors.append(
            {
                "factor": "missed_doses_last_30_days",
                "value": patient["missed_doses_last_30_days"],
                "impact": "high",
                "explanation": "Patient has a high number of missed doses in the last 30 days.",
            }
        )
    elif patient["missed_doses_last_30_days"] >= 3:
        factors.append(
            {
                "factor": "missed_doses_last_30_days",
                "value": patient["missed_doses_last_30_days"],
                "impact": "medium",
                "explanation": "Patient has a moderate number of missed doses.",
            }
        )

    if refill_delay > 7:
        factors.append(
            {
                "factor": "last_refill_days_ago",
                "value": patient["last_refill_days_ago"],
                "impact": "high",
                "explanation": "Medication refill appears significantly overdue.",
            }
        )
    elif refill_delay > 0:
        factors.append(
            {
                "factor": "last_refill_days_ago",
                "value": patient["last_refill_days_ago"],
                "impact": "medium",
                "explanation": "Medication refill appears slightly overdue.",
            }
        )

    if patient["prior_non_adherence"]:
        factors.append(
            {
                "factor": "prior_non_adherence",
                "value": True,
                "impact": "medium",
                "explanation": "Patient has previous non-adherence history.",
            }
        )

    if patient["age"] >= 65:
        factors.append(
            {
                "factor": "age",
                "value": patient["age"],
                "impact": "low",
                "explanation": "Older patients may require more adherence support.",
            }
        )

    if not factors:
        factors.append(
            {
                "factor": "overall_profile",
                "value": "stable",
                "impact": "low",
                "explanation": "Patient profile does not show major adherence risk drivers.",
            }
        )

    impact_order = {"high": 3, "medium": 2, "low": 1}
    factors.sort(key=lambda item: impact_order[item["impact"]], reverse=True)

    return factors[:4]


def risk_agent(state: dict) -> dict:
    patient = state["patient"]

    features = pd.DataFrame(
        [
            {
                "age": patient["age"],
                "last_refill_days_ago": patient["last_refill_days_ago"],
                "supply_days": patient["supply_days"],
                "missed_doses_last_30_days": patient["missed_doses_last_30_days"],
                "prior_non_adherence": int(patient["prior_non_adherence"]),
            }
        ],
        columns=FEATURES,
    )

    risk_score = float(model.predict_proba(features)[0][1])

    if risk_score >= 0.7:
        risk_level = "high"
    elif risk_score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    top_factors = build_top_factors(patient)
    reasons = [factor["explanation"] for factor in top_factors]
    reasons.append(f"ML model estimated non-adherence probability at {round(risk_score, 2)}.")

    return {
        "risk": {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "reasons": reasons,
            "top_factors": top_factors,
            "model_type": model.__class__.__name__,
        }
    }