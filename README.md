# Sentry — Fraud Detection App

A Flask app that scores transactions for fraud risk using a scikit-learn
model, with three views: a single-transaction checker, CSV batch upload, and
a stats dashboard.

## Structure

```
fraud-app/
├── backend/
│   ├── app.py              # Flask app (routes, scoring, dashboard API)
│   ├── train_model.py      # Trains and saves the model
│   ├── generate_data.py    # Generates synthetic sample data
│   ├── requirements.txt
│   ├── Procfile
│   ├── data/
│   │   └── sample_transactions.csv
│   └── models/
│       ├── fraud_model.joblib
│       └── metrics.json
└── frontend/
    ├── templates/
    │   ├── base.html
    │   ├── index.html      # Single-transaction check
    │   ├── batch.html      # CSV batch upload
    │   └── dashboard.html
    └── static/
        ├── css/style.css
        └── js/
            ├── single.js
            ├── batch.js
            └── dashboard.js
```

`app.py` lives in `backend/` but points Flask's `template_folder` and
`static_folder` at `../frontend/templates` and `../frontend/static`, so the
two halves stay decoupled while still served by the one Flask process.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 1. (Optional) Regenerate sample data

```bash
python generate_data.py
```

## 2. Train the model

```bash
python train_model.py
```

Reads `backend/data/sample_transactions.csv`, trains a Random Forest
classifier, and writes `backend/models/fraud_model.joblib` and
`backend/models/metrics.json`.

## 3. Run the app

```bash
python app.py
```

Open http://localhost:5000 — Flask serves the frontend templates/static from
the `frontend/` folder automatically.

## Using your own data

Replace `backend/data/sample_transactions.csv` with your own CSV containing
at least these columns, then re-run `train_model.py`:

| column | type | notes |
|---|---|---|
| amount | float | transaction amount |
| transaction_type | string | e.g. purchase, withdrawal, transfer, online, refund |
| hour | int | hour of day, 0–23 |
| distance_from_home_km | float | distance from account's home location |
| distance_from_last_txn_km | float | distance from the previous transaction |
| account_age_days | int | age of the account in days |
| num_txns_last_24h | int | transaction count in the last 24 hours |
| is_foreign | 0/1 | foreign transaction flag |
| is_high_risk_merchant | 0/1 | high-risk merchant category flag |
| is_fraud | 0/1 | label — required for training only |

The batch upload page expects the same columns (minus `is_fraud`).

## Deploying (git → GitHub → Render)

1. From the project root: `git init`, `git add .`, `git commit -m "Initial commit"`.
2. Create an empty GitHub repo, then `git remote add origin <url>`, `git push -u origin main`.
3. On Render: New → Web Service → connect the repo.
4. **Root Directory**: set to `backend` (Render needs this since `app.py`,
   `requirements.txt`, and the `Procfile` all live there).
5. Build command: `pip install -r requirements.txt`. Start command: leave
   blank to use the `Procfile`, or set explicitly to
   `gunicorn app:app --bind 0.0.0.0:$PORT`.
6. Deploy — Render gives you a live URL, and redeploys automatically on
   every push to `main`.

## Notes

- The model is a `RandomForestClassifier` inside a scikit-learn `Pipeline`
  (scaling + one-hot encoding included), saved with `joblib`.
- The synthetic sample data has a clean separation between fraud/legit
  patterns, so the sample model scores ~100% on held-out data. Real-world
  data will be noisier — retrain on your own data before relying on this.
- Batch results live in server memory between upload and download; for
  production use, persist results to disk or a database instead.
