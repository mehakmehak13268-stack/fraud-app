"""
Fraud Detection App - Flask backend.

Routes:
  GET  /            -> single-transaction check form
  POST /predict      -> JSON prediction for one transaction
  GET  /batch        -> CSV batch upload page
  POST /batch/upload  -> processes uploaded CSV, returns results page
  GET  /dashboard     -> stats dashboard over data/sample_transactions.csv
  GET  /api/dashboard -> JSON stats used by dashboard charts
"""
import io
import json
import os

import joblib
import pandas as pd
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))          # .../backend
PROJECT_ROOT = os.path.dirname(APP_DIR)                        # project root
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

MODEL_PATH = os.path.join(APP_DIR, "models", "fraud_model.joblib")
METRICS_PATH = os.path.join(APP_DIR, "models", "metrics.json")
DATA_PATH = os.path.join(APP_DIR, "data", "sample_transactions.csv")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload cap

_model_bundle = None


def get_model_bundle():
    """Lazy-load the trained model bundle (pipeline + feature metadata)."""
    global _model_bundle
    if _model_bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "No trained model found. Run `python train_model.py` first."
            )
        _model_bundle = joblib.load(MODEL_PATH)
    return _model_bundle


def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Adds fraud_probability and is_flagged columns to a dataframe of transactions."""
    bundle = get_model_bundle()
    pipeline = bundle["pipeline"]
    numeric = bundle["numeric_features"]
    categorical = bundle["categorical_features"]

    missing = [c for c in numeric + categorical if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    X = df[numeric + categorical].copy()
    probs = pipeline.predict_proba(X)[:, 1]
    out = df.copy()
    out["fraud_probability"] = probs.round(4)
    out["is_flagged"] = out["fraud_probability"] >= 0.5
    return out


# ---------------------------------------------------------------- pages ----

@app.route("/")
def index():
    return render_template("index.html", active="single")


@app.route("/batch")
def batch_page():
    return render_template("batch.html", active="batch")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active="dashboard")


# --------------------------------------------------------------- api -------

@app.route("/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json(force=True)
        row = {
            "amount": float(payload.get("amount", 0)),
            "transaction_type": payload.get("transaction_type", "purchase"),
            "hour": int(payload.get("hour", 12)),
            "distance_from_home_km": float(payload.get("distance_from_home_km", 0)),
            "distance_from_last_txn_km": float(
                payload.get("distance_from_last_txn_km", 0)
            ),
            "account_age_days": int(payload.get("account_age_days", 365)),
            "num_txns_last_24h": int(payload.get("num_txns_last_24h", 1)),
            "is_foreign": int(payload.get("is_foreign", 0)),
            "is_high_risk_merchant": int(payload.get("is_high_risk_merchant", 0)),
        }
        df = pd.DataFrame([row])
        scored = score_dataframe(df)
        prob = float(scored.loc[0, "fraud_probability"])

        if prob >= 0.75:
            risk_level = "high"
        elif prob >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        return jsonify(
            {
                "fraud_probability": prob,
                "is_flagged": bool(scored.loc[0, "is_flagged"]),
                "risk_level": risk_level,
            }
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 400


@app.route("/batch/upload", methods=["POST"])
def batch_upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded."}), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Please upload a .csv file."}), 400

    try:
        df = pd.read_csv(file)
        scored = score_dataframe(df)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Could not process file: {e}"}), 400

    n_flagged = int(scored["is_flagged"].sum())
    summary = {
        "n_rows": len(scored),
        "n_flagged": n_flagged,
        "flag_rate": round(n_flagged / len(scored), 4) if len(scored) else 0,
    }

    # stash results in-memory keyed by a token so the client can download the CSV
    global _last_batch_result
    _last_batch_result = scored

    preview = scored.sort_values("fraud_probability", ascending=False).head(200)
    return jsonify(
        {
            "summary": summary,
            "rows": json.loads(preview.to_json(orient="records")),
        }
    )


_last_batch_result = None


@app.route("/batch/download")
def batch_download():
    global _last_batch_result
    if _last_batch_result is None:
        return jsonify({"error": "No batch result available yet."}), 404
    buf = io.StringIO()
    _last_batch_result.to_csv(buf, index=False)
    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="fraud_scored_transactions.csv",
    )


@app.route("/api/dashboard")
def api_dashboard():
    metrics = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH) as f:
            metrics = json.load(f)

    if not os.path.exists(DATA_PATH):
        return jsonify({"metrics": metrics, "error": "No sample data found."})

    df = pd.read_csv(DATA_PATH)
    scored = score_dataframe(df)

    by_hour = (
        scored.groupby("hour")["is_flagged"].mean().reindex(range(24), fill_value=0)
    )
    by_type = scored.groupby("transaction_type")["is_flagged"].mean()
    amount_bins = pd.cut(
        scored["amount"], bins=[0, 50, 150, 400, 1000, 1e9],
        labels=["0-50", "50-150", "150-400", "400-1000", "1000+"],
    )
    by_amount = scored.groupby(amount_bins, observed=True)["is_flagged"].mean()

    return jsonify(
        {
            "metrics": metrics,
            "totals": {
                "n_transactions": len(scored),
                "n_flagged": int(scored["is_flagged"].sum()),
                "avg_amount": round(float(scored["amount"].mean()), 2),
                "avg_flagged_amount": round(
                    float(scored.loc[scored["is_flagged"], "amount"].mean() or 0), 2
                ),
            },
            "by_hour": {str(k): round(float(v), 4) for k, v in by_hour.items()},
            "by_type": {str(k): round(float(v), 4) for k, v in by_type.items()},
            "by_amount": {str(k): round(float(v), 4) for k, v in by_amount.items()},
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host="0.0.0.0", port=port)
