"""
Vercel serverless endpoint: POST /api/predict

Lightweight, dependency-free port of the rule-based scorer in app.py.
The real trained DNN/LSTM ensemble (model/*.h5) needs TensorFlow, which is
far too large to ship in a serverless function, so the hosted demo scores
transactions with the same heuristic app.py falls back to when the ML
models aren't available. Run app.py locally (see README) for real
model inference.
"""
import json
import math
from http.server import BaseHTTPRequestHandler


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def rule_based(amount, hour, velocity, is_new, is_vpn,
               sim_swap, num_meters, fail_logins, distance, account_age):
    night = 1.0 if (hour < 6 or hour >= 22) else 0.0
    base = (
        clamp(math.log1p(amount) / 13.0) * 0.24 +
        clamp(velocity / 20.0) * 0.16 +
        is_vpn * 0.16 +
        sim_swap * 0.14 +
        is_new * 0.10 +
        night * 0.08 +
        clamp(fail_logins / 8.0) * 0.06 +
        clamp(num_meters / 10.0) * 0.04 +
        (1.0 - clamp(account_age / 3650.0)) * 0.04 +
        clamp(distance / 500.0) * 0.02
    )
    dnn_p = clamp(base * 0.95 + 0.02)
    lstm_p = clamp(base * 0.90 + 0.04)
    ensemble = dnn_p * 0.6 + lstm_p * 0.4
    return dnn_p, lstm_p, ensemble


def predict(raw):
    amount = float(raw.get("amount", 0) or 0)
    hour = int(raw.get("hour", 0) or 0)
    velocity = int(raw.get("velocity", 0) or 0)
    is_new = int(raw.get("is_new_device", 0) or 0)
    is_vpn = int(raw.get("is_vpn", 0) or 0)
    sim_swap = int(raw.get("sim_swap", 0) or 0)
    num_meters = int(raw.get("num_meters", 0) or 0)
    fail_logins = int(raw.get("fail_logins", 0) or 0)
    distance = float(raw.get("distance", 0) or 0)
    account_age = int(raw.get("account_age", 0) or 0)

    dnn_p, lstm_p, ensemble = rule_based(
        amount, hour, velocity, is_new, is_vpn,
        sim_swap, num_meters, fail_logins, distance, account_age,
    )

    fraud = ensemble >= 0.5
    level = "HIGH" if ensemble > 0.7 else "MEDIUM" if ensemble > 0.4 else "LOW"
    color = "#E24B4A" if level == "HIGH" else "#BA7517" if level == "MEDIUM" else "#639922"
    return {
        "success": True,
        "fraud": bool(fraud),
        "probability": round(ensemble * 100, 2),
        "dnn_prob": round(dnn_p * 100, 2),
        "lstm_prob": round(lstm_p * 100, 2),
        "risk_level": level,
        "risk_color": color,
        "verdict": "FRAUDULENT" if fraud else "LEGITIMATE",
    }


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(body or "{}")
            result = predict(data)
            code = 200
        except Exception as exc:
            result = {"success": False, "error": str(exc)}
            code = 400

        payload = json.dumps(result).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)
