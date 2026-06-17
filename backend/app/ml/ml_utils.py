import json
import os

import joblib
import pandas as pd


ML_DIR = os.path.dirname(__file__)

FEATURES = [
    "age",
    "last_refill_days_ago",
    "supply_days",
    "missed_doses_last_30_days",
    "prior_non_adherence",
]


def read_json_file(filename: str):
    path = os.path.join(ML_DIR, filename)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_patient_feature_dataframe(patient) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "age": patient.age,
                "last_refill_days_ago": patient.last_refill_days_ago,
                "supply_days": patient.supply_days,
                "missed_doses_last_30_days": patient.missed_doses_last_30_days,
                "prior_non_adherence": int(patient.prior_non_adherence),
            }
        ],
        columns=FEATURES,
    )


def load_cluster_assets():
    cluster_model = joblib.load(os.path.join(ML_DIR, "cluster_model.pkl"))
    scaler = joblib.load(os.path.join(ML_DIR, "cluster_scaler.pkl"))
    return cluster_model, scaler