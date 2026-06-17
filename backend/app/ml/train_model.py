import json
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "age",
    "last_refill_days_ago",
    "supply_days",
    "missed_doses_last_30_days",
    "prior_non_adherence",
]

MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "model_metrics.json")
COMPARISON_PATH = os.path.join(MODEL_DIR, "model_comparison.json")
FEATURE_IMPORTANCE_PATH = os.path.join(MODEL_DIR, "feature_importance.json")
REGISTRY_PATH = os.path.join(MODEL_DIR, "model_registry.json")
DRIFT_BASELINE_PATH = os.path.join(MODEL_DIR, "drift_baseline.json")
CLUSTER_MODEL_PATH = os.path.join(MODEL_DIR, "cluster_model.pkl")
CLUSTER_SCALER_PATH = os.path.join(MODEL_DIR, "cluster_scaler.pkl")


def generate_synthetic_training_data(n: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    rows = []

    for _ in range(n):
        age = int(rng.integers(22, 90))
        supply_days = int(rng.choice([30, 60, 90], p=[0.72, 0.18, 0.10]))

        prior_non_adherence = int(rng.choice([0, 1], p=[0.72, 0.28]))

        base_refill = rng.normal(loc=supply_days - 4, scale=12)
        if prior_non_adherence:
            base_refill += rng.normal(loc=8, scale=6)

        last_refill_days_ago = int(max(1, min(110, round(base_refill))))

        missed_base = rng.poisson(2)
        if last_refill_days_ago > supply_days:
            missed_base += rng.poisson(3)
        if prior_non_adherence:
            missed_base += rng.poisson(2)
        if age >= 65:
            missed_base += rng.choice([0, 1, 2], p=[0.5, 0.35, 0.15])

        missed_doses = int(max(0, min(30, missed_base)))

        refill_delay = max(0, last_refill_days_ago - supply_days)

        risk_signal = (
            0.35 * (missed_doses >= 5)
            + 0.30 * (refill_delay >= 5)
            + 0.20 * prior_non_adherence
            + 0.10 * (age >= 65)
            + 0.05 * (last_refill_days_ago >= supply_days - 3)
        )

        noise = rng.normal(0, 0.08)
        non_adherent = int((risk_signal + noise) >= 0.42)

        rows.append(
            {
                "age": age,
                "last_refill_days_ago": last_refill_days_ago,
                "supply_days": supply_days,
                "missed_doses_last_30_days": missed_doses,
                "prior_non_adherence": prior_non_adherence,
                "non_adherent": non_adherent,
            }
        )

    return pd.DataFrame(rows)


def evaluate_model(model, X_test, y_test) -> dict:
    predictions = model.predict(X_test)

    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
    }


def get_feature_importance(model, model_name: str) -> list[dict]:
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    else:
        importances = np.zeros(len(FEATURES))

    total = float(np.sum(importances))

    if total > 0:
        normalized = importances / total
    else:
        normalized = importances

    items = [
        {
            "feature": feature,
            "importance": round(float(importance), 4),
        }
        for feature, importance in zip(FEATURES, normalized)
    ]

    return sorted(items, key=lambda x: x["importance"], reverse=True)


def train_cluster_model(df: pd.DataFrame):
    X = df[FEATURES]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    cluster_model = KMeans(n_clusters=4, random_state=42, n_init=10)
    cluster_model.fit(X_scaled)

    joblib.dump(cluster_model, CLUSTER_MODEL_PATH)
    joblib.dump(scaler, CLUSTER_SCALER_PATH)


def create_drift_baseline(df: pd.DataFrame):
    baseline = {}

    for feature in FEATURES:
        baseline[feature] = {
            "mean": round(float(df[feature].mean()), 4),
            "std": round(float(df[feature].std()), 4),
        }

    with open(DRIFT_BASELINE_PATH, "w", encoding="utf-8") as file:
        json.dump(baseline, file, indent=2)


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)

    df = generate_synthetic_training_data()

    X = df[FEATURES]
    y = df["non_adherent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=180,
            max_depth=8,
            random_state=42,
            class_weight="balanced",
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            random_state=42,
            n_estimators=140,
            learning_rate=0.06,
            max_depth=3,
        ),
    }

    comparison = []

    best_name = None
    best_model = None
    best_metrics = None

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)

        comparison.append(
            {
                "model": name,
                **metrics,
            }
        )

        if best_metrics is None or metrics["f1_score"] > best_metrics["f1_score"]:
            best_name = name
            best_model = model
            best_metrics = metrics

    feature_importance = get_feature_importance(best_model, best_name)

    joblib.dump(best_model, MODEL_PATH)

    timestamp = datetime.now(timezone.utc).isoformat()
    version = f"v{timestamp.replace(':', '').replace('-', '').split('.')[0]}"

    model_metrics = {
        "model_type": best_name,
        "active_version": version,
        "training_data_type": "synthetic",
        "training_rows": int(len(df)),
        "features": FEATURES,
        **best_metrics,
        "notes": "Synthetic demo model. Not intended for clinical use.",
        "trained_at": timestamp,
    }

    model_comparison = {
        "best_model": best_name,
        "selected_by": "f1_score",
        "models": comparison,
    }

    model_registry = {
        "active_model": "risk_model.pkl",
        "active_version": version,
        "models": [
            {
                "version": version,
                "model_file": "risk_model.pkl",
                "model_type": best_name,
                **best_metrics,
                "created_at": timestamp,
            }
        ],
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as file:
        json.dump(model_metrics, file, indent=2)

    with open(COMPARISON_PATH, "w", encoding="utf-8") as file:
        json.dump(model_comparison, file, indent=2)

    with open(FEATURE_IMPORTANCE_PATH, "w", encoding="utf-8") as file:
        json.dump(feature_importance, file, indent=2)

    with open(REGISTRY_PATH, "w", encoding="utf-8") as file:
        json.dump(model_registry, file, indent=2)

    create_drift_baseline(df)
    train_cluster_model(df)

    print("Training complete.")
    print(f"Best model: {best_name}")
    print(f"Metrics: {best_metrics}")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved comparison to: {COMPARISON_PATH}")
    print(f"Saved feature importance to: {FEATURE_IMPORTANCE_PATH}")
    print(f"Saved model registry to: {REGISTRY_PATH}")
    print(f"Saved drift baseline to: {DRIFT_BASELINE_PATH}")
    print(f"Saved cluster model to: {CLUSTER_MODEL_PATH}")


if __name__ == "__main__":
    train()