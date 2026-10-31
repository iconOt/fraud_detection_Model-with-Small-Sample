
import os
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest


# --------------------------------------------------
# 1. Application configuration
# --------------------------------------------------

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # 16 KB maximum request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set FRONTEND_ORIGINS in your environment, separated by commas.
# Example: http://localhost:5173,https://your-frontend.example.com
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173"
    ).split(",")
    if origin.strip()
]

CORS(app, resources={
    r"/api/*": {"origins": allowed_origins}
})


# --------------------------------------------------
# 2. Load the trained model
# --------------------------------------------------

MODEL_PATH = Path(__file__).resolve().parent / "fraud_model.joblib"

try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    raise RuntimeError(
        f"Model file not found: {MODEL_PATH}. "
        "Ensure fraud_model.joblib is included in the deployment."
    )
except Exception as exc:
    raise RuntimeError(
        f"Could not load the fraud detection model: {exc}"
    ) from exc


# --------------------------------------------------
# 3. Feature mappings
# Must match the training script exactly.
# --------------------------------------------------

TRANSACTION_TYPE_MAP = {
    "ATM": 0,
    "POS": 1,
    "ONLINE": 2
}

LOCATION_MAP = {
    "ABUJA": 0,
    "LAGOS": 1,
    "KANO": 2,
    "OTHERS": 3
}


# --------------------------------------------------
# 4. Health check
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None
    }), 200


# --------------------------------------------------
# 5. Fraud prediction
# --------------------------------------------------

@app.route("/api/predict", methods=["POST"])
def predict():
    # Validate JSON content type and body.
    if not request.is_json:
        return jsonify({
            "error": "Content-Type must be application/json."
        }), 415

    try:
        data = request.get_json()
    except BadRequest:
        return jsonify({
            "error": "Request body contains invalid JSON."
        }), 400

    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON body must be an object."
        }), 400

    required_fields = [
        "amount",
        "time",
        "transaction_type",
        "location"
    ]

    missing_fields = [
        field for field in required_fields
        if field not in data
        or data[field] is None
        or (isinstance(data[field], str) and not data[field].strip())
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields.",
            "fields": missing_fields
        }), 400

    try:
        # Reject booleans and non-numeric values.
        if isinstance(data["amount"], bool):
            raise ValueError("amount must be a number.")

        if isinstance(data["time"], bool):
            raise ValueError("time must be a number.")

        amount = float(data["amount"])
        transaction_time = float(data["time"])

        if not np.isfinite(amount) or amount < 0:
            raise ValueError(
                "amount must be a finite, non-negative number."
            )

        if (
            not np.isfinite(transaction_time)
            or not transaction_time.is_integer()
            or not 0 <= transaction_time <= 86399
        ):
            raise ValueError(
                "time must be an integer between 0 and 86399."
            )

        transaction_type = str(
            data["transaction_type"]
        ).strip().upper()

        location = str(data["location"]).strip().upper()

        if transaction_type not in TRANSACTION_TYPE_MAP:
            return jsonify({
                "error": "Unsupported transaction_type.",
                "allowed_values": ["ATM", "POS", "Online"]
            }), 400

        if location not in LOCATION_MAP:
            return jsonify({
                "error": "Unsupported location.",
                "allowed_values": [
                    "Abuja", "Lagos", "Kano", "Others"
                ]
            }), 400

        # IMPORTANT:
        # The previous training pipeline expects these named columns.
        features = pd.DataFrame([{
            "amount": amount,
            "time": int(transaction_time),
            "transaction_type": TRANSACTION_TYPE_MAP[
                transaction_type
            ],
            "location_code": LOCATION_MAP[location]
        }])

        # Generate prediction.
        prediction = int(model.predict(features)[0])

        # Find the probability belonging to class 1 (fraud).
        fraud_probability = None

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features)[0]
            classes = list(model.classes_)

            if 1 in classes:
                fraud_probability = float(
                    probabilities[classes.index(1)]
                )

        response = {
            "prediction": (
                "fraudulent" if prediction == 1
                else "legitimate"
            ),
            "fraud_probability": (
                round(fraud_probability, 4)
                if fraud_probability is not None
                else None
            ),
            "model_version": "1.0"
        }

        return jsonify(response), 200

    except (TypeError, ValueError) as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception:
        logger.exception("Fraud prediction failed.")

        return jsonify({
            "error": "Prediction failed due to an internal server error."
        }), 500


# --------------------------------------------------
# 6. Application entry point
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
 