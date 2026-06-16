import os
import joblib
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def build_training_data():
    data = [
        # age, last_refill_days_ago, supply_days, missed_doses, prior_non_adherence, label
        [45, 22, 30, 1, 0, 0],
        [34, 18, 30, 0, 0, 0],
        [52, 27, 30, 2, 0, 0],
        [41, 25, 30, 1, 0, 0],
        [60, 29, 30, 3, 0, 0],

        [58, 33, 30, 4, 0, 1],
        [67, 41, 30, 6, 1, 1],
        [72, 52, 30, 9, 1, 1],
        [49, 44, 30, 7, 1, 1],
        [63, 37, 30, 6, 0, 1],
        [70, 31, 30, 5, 1, 1],
        [56, 39, 30, 8, 0, 1],

        [44, 30, 30, 3, 0, 0],
        [38, 28, 30, 2, 0, 0],
        [75, 35, 30, 4, 1, 1],
        [66, 26, 30, 2, 1, 0],
        [69, 45, 30, 5, 1, 1],
        [50, 32, 30, 5, 0, 1],
        [47, 21, 30, 0, 1, 0],
        [80, 50, 30, 10, 1, 1],
    ]

    columns = [
        "age",
        "last_refill_days_ago",
        "supply_days",
        "missed_doses_last_30_days",
        "prior_non_adherence",
        "non_adherent",
    ]

    return pd.DataFrame(data, columns=columns)


def train():
    df = build_training_data()

    X = df[
        [
            "age",
            "last_refill_days_ago",
            "supply_days",
            "missed_doses_last_30_days",
            "prior_non_adherence",
        ]
    ]

    y = df["non_adherent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print("Model evaluation:")
    print(classification_report(y_test, predictions))

    model_path = os.path.join(os.path.dirname(__file__), "risk_model.pkl")
    joblib.dump(model, model_path)

    print(f"Saved model to: {model_path}")


if __name__ == "__main__":
    train()