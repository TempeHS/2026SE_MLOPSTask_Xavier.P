from flask import Flask, render_template, request, jsonify
from flask_wtf import CSRFProtect
import logging
import pickle
import numpy as np
import os

app_log = logging.getLogger(__name__)
logging.basicConfig(
    filename="security_log.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
)

app = Flask(__name__)
app.secret_key = b"_5TvTgyH61Hn1pr9v;apl"
csrf = CSRFProtect(app)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["WTF_CSRF_CHECK_DEFAULT"] = False

CSP_POLICY = {
    "base-uri": "'self'",
    "default-src": "'self'",
    "style-src": "'self'",
    "script-src": "'self'",
    "img-src": "'self' data:",
    "media-src": "'self'",
    "font-src": "'self'",
    "object-src": "'self'",
    "child-src": "'self'",
    "connect-src": "'self'",
    "worker-src": "'self'",
    "report-uri": "/csp_report",
    "frame-ancestors": "'none'",
    "form-action": "'self'",
    "frame-src": "'none'",
}

FEATURE_COLS = [
    "energy",
    "danceability",
    "acousticness",
    "valence",
    "loudness",
    "tempo",
    "track_popularity",
    "speechiness",
    "instrumentalness",
    "liveness",
    "duration_ms",
]

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../3.Operations/3.1.Deploy_Model/my_saved_model_v4.sav",
)


def load_model():
    """Load and return the Random Forest model from the deploy directory."""
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


try:
    model = load_model()
    app_log.info("Random Forest model loaded successfully")
except FileNotFoundError:
    model = None
    app_log.error("Model file not found at: %s", MODEL_PATH)


@app.after_request
def apply_csp(response):
    """Apply Content Security Policy headers to all responses."""
    policy = "; ".join(f"{key} {value}" for key, value in CSP_POLICY.items())
    response.headers["Content-Security-Policy"] = policy
    return response


@app.route("/", methods=["GET"])
def index():
    """Render the main prediction UI page."""
    return render_template("index.html", features=FEATURE_COLS)


@app.route("/predict", methods=["POST"])
@csrf.exempt
def predict():
    """
    Accept feature inputs and return a release year prediction from the Random Forest model.
    Expects JSON with all 11 feature values.
    Returns a JSON object with the predicted release year.
    """
    if model is None:
        app_log.error("Predict called but model is not loaded")
        return jsonify({"error": "Model not loaded"}), 503

    data = request.get_json(force=True, silent=True)
    if not data:
        app_log.warning("Predict endpoint called with no JSON data")
        return jsonify({"error": "No input data provided"}), 400

    try:
        features = [float(data.get(col, 0)) for col in FEATURE_COLS]
    except (ValueError, TypeError) as e:
        app_log.warning("Invalid feature input: %s", e)
        return jsonify({"error": "Invalid feature values"}), 400

    x = np.array([features])
    prediction = round(float(model.predict(x)[0]), 2)

    app_log.info("Prediction made: %s -> %s", features, prediction)
    return jsonify({"prediction": prediction})


@app.route("/privacy.html", methods=["GET"])
def privacy():
    """Render the privacy policy page."""
    return render_template("privacy.html")


@app.route("/csp_report", methods=["POST"])
@csrf.exempt
def csp_report():
    """Receive and log Content Security Policy violation reports."""
    app.logger.critical(request.data.decode())
    return "done"


if __name__ == "__main__":
    port = 5000
    print(f" * Running on http://0.0.0.0:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)
