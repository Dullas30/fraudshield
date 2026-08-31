"""
Vercel serverless endpoint: GET /api/live_feed?count=N

Generates simulated transactions and scores them with the same
dependency-free heuristic as api/predict.py, mirroring app.py's
random_tx() for the local demo.
"""
import json
import math
import random
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

DISCOS = ["AEDC", "EKEDC", "IKEDC", "EEDC", "PHEDC", "JEDC", "BEDC", "KAEDCO", "KEDCO", "YEDC", "IBEDC"]
STATES = ["Abuja", "Lagos", "Rivers", "Kano", "Kaduna", "Enugu", "Imo", "Oyo", "Delta", "Edo", "Borno"]
CHANNELS = ["web", "mobile_app", "ussd", "agent", "pos"]


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


def random_tx():
    fraud = random.random() < 0.09
    disco = random.choice(DISCOS)
    state = random.choice(STATES)
    channel = random.choice(CHANNELS)
    if fraud:
        amount = random.randint(50000, 300000)
        raw = dict(amount=amount, hour=random.choice(list(range(6)) + list(range(22, 24))),
                   velocity=random.randint(8, 25), is_new_device=random.choice([0, 1, 1]),
                   is_vpn=random.choice([0, 1, 1]), sim_swap=random.choice([0, 1]),
                   num_meters=random.randint(3, 12), fail_logins=random.randint(3, 8),
                   distance=round(random.uniform(50, 500), 1), account_age=random.randint(1, 60))
    else:
        amount = random.randint(500, 25000)
        raw = dict(amount=amount, hour=random.randint(7, 21),
                   velocity=random.randint(1, 3), is_new_device=random.choice([0, 0, 0, 1]),
                   is_vpn=random.choice([0, 0, 0, 1]), sim_swap=0,
                   num_meters=random.randint(1, 2), fail_logins=random.randint(0, 1),
                   distance=round(random.uniform(0, 15), 1), account_age=random.randint(100, 2000))
    result = predict(raw)
    return {
        "id": "TXN" + "".join(str(random.randint(0, 9)) for _ in range(7)),
        "disco": disco, "state": state, "channel": channel,
        "amount": f"NGN {amount:,}",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        **result,
    }


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        try:
            count = max(1, min(50, int(qs.get("count", ["5"])[0])))
        except ValueError:
            count = 5

        payload = json.dumps([random_tx() for _ in range(count)]).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)
