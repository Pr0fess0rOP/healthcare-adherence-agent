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

CLUSTER_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ml",
    "cluster_model.pkl",
)

CLUSTER_SCALER_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ml",
    "cluster_scaler.pkl",
)

cluster_model = joblib.load(CLUSTER_MODEL_PATH)
scaler = joblib.load(CLUSTER_SCALER_PATH)


SEGMENT_LABELS = {
    0: "Stable adherence profile",
    1: "Refill delay monitor",
    2: "Missed-dose support needed",
    3: "High-touch adherence support",
}


def segment_agent(state: dict) -> dict:
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

    scaled = scaler.transform(features)
    cluster_id = int(cluster_model.predict(scaled)[0])

    return {
        "segment": {
            "cluster_id": cluster_id,
            "label": SEGMENT_LABELS.get(cluster_id, "General adherence monitoring"),
            "method": "KMeans",
        }
    }