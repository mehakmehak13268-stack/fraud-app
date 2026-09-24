"""
Generates a synthetic sample_transactions.csv for the fraud detection app.
Run once: python generate_data.py
"""
import os

import numpy as np
import pandas as pd

APP_DIR = os.path.dirname(os.path.abspath(__file__))

np.random.seed(42)

N = 3000
FRAUD_RATE = 0.06

n_fraud = int(N * FRAUD_RATE)
n_legit = N - n_fraud

txn_types = ["purchase", "withdrawal", "transfer", "online", "refund"]


def make_legit(n):
    return pd.DataFrame({
        "amount": np.round(np.random.gamma(shape=2.0, scale=45, size=n), 2),
        "transaction_type": np.random.choice(txn_types, n, p=[0.4, 0.15, 0.15, 0.25, 0.05]),
        "hour": np.random.normal(14, 4, n).clip(0, 23).astype(int),
        "distance_from_home_km": np.round(np.random.exponential(8, n), 2),
        "distance_from_last_txn_km": np.round(np.random.exponential(5, n), 2),
        "account_age_days": np.random.randint(30, 3650, n),
        "num_txns_last_24h": np.random.poisson(2, n),
        "is_foreign": np.random.choice([0, 1], n, p=[0.93, 0.07]),
        "is_high_risk_merchant": np.random.choice([0, 1], n, p=[0.9, 0.1]),
        "is_fraud": 0
    })


def make_fraud(n):
    return pd.DataFrame({
        "amount": np.round(np.random.gamma(shape=3.0, scale=180, size=n), 2),
        "transaction_type": np.random.choice(txn_types, n, p=[0.15, 0.15, 0.3, 0.35, 0.05]),
        "hour": np.random.choice(list(range(0, 6)) + list(range(22, 24)), n),
        "distance_from_home_km": np.round(np.random.exponential(400, n), 2),
        "distance_from_last_txn_km": np.round(np.random.exponential(250, n), 2),
        "account_age_days": np.random.randint(1, 400, n),
        "num_txns_last_24h": np.random.poisson(9, n),
        "is_foreign": np.random.choice([0, 1], n, p=[0.35, 0.65]),
        "is_high_risk_merchant": np.random.choice([0, 1], n, p=[0.4, 0.6]),
        "is_fraud": 1
    })


df = pd.concat([make_legit(n_legit), make_fraud(n_fraud)], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df.insert(0, "transaction_id", [f"TXN{100000+i}" for i in range(len(df))])

out_path = os.path.join(APP_DIR, "data", "sample_transactions.csv")
df.to_csv(out_path, index=False)
print(f"Wrote {out_path} with {len(df)} rows ({df['is_fraud'].sum()} fraud)")
