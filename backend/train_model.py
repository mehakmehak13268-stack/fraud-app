"""
Trains a fraud-detection classifier on data/sample_transactions.csv
and saves the fitted pipeline (encoder + scaler + model) to models/fraud_model.joblib

Run: python train_model.py
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_DIR, "data", "sample_transactions.csv")
MODEL_PATH = os.path.join(APP_DIR, "models", "fraud_model.joblib")
METRICS_PATH = os.path.join(APP_DIR, "models", "metrics.json")

NUMERIC_FEATURES = [
    "amount",
    "hour",
    "distance_from_home_km",
    "distance_from_last_txn_km",
    "account_age_days",
    "num_txns_last_24h",
    "is_foreign",
    "is_high_risk_merchant",
]
CATEGORICAL_FEATURES = ["transaction_type"]
TARGET = "is_fraud"


def main():
    df = pd.read_csv(DATA_PATH)

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", clf)])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, y_pred, output_dict=True)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("Classification report:")
    print(classification_report(y_test, y_pred))
    print(f"ROC AUC: {auc:.4f}")
    print(f"Confusion matrix: {cm}")

    joblib.dump(
        {
            "pipeline": pipeline,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "transaction_types": sorted(df["transaction_type"].unique().tolist()),
        },
        MODEL_PATH,
    )

    metrics = {
        "roc_auc": auc,
        "confusion_matrix": cm,
        "precision_fraud": report["1"]["precision"],
        "recall_fraud": report["1"]["recall"],
        "f1_fraud": report["1"]["f1-score"],
        "n_train": len(X_train),
        "n_test": len(X_test),
        "fraud_rate": float(df[TARGET].mean()),
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved model to {MODEL_PATH}")
    print(f"Saved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
