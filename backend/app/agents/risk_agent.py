import os
import joblib
import pandas as pd


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ml",
    "risk_model.pkl",
)

model = joblib.load(MODEL_PATH)


def build_reasons(patient: dict, risk_score: float) -> list[str]:
    reasons = []

    if patient["last_refill_days_ago"] > patient["supply_days"]:
        reasons.append("Refill is overdue")

    if patient["missed_doses_last_30_days"] > 5:
        reasons.append("High number of missed doses in last 30 days")

    if patient["prior_non_adherence"]:
        reasons.append("Patient has prior non-adherence history")

    if patient["age"] >= 65:
        reasons.append("Patient is 65 or older")

    if not reasons:
        reasons.append(
            "Model predicted lower risk based on refill timing, missed doses, age, and prior adherence history"
        )

    reasons.append(
        f"ML model estimated non-adherence probability at {round(risk_score, 2)}"
    )

    return reasons


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
        ]
    )

    risk_score = float(model.predict_proba(features)[0][1])

    if risk_score >= 0.7:
        risk_level = "high"
    elif risk_score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk": {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "reasons": build_reasons(patient, risk_score),
            "model_type": "LogisticRegression",
        }
    }