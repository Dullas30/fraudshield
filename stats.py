"""
Vercel serverless endpoint: GET /api/stats

Returns the same realistic placeholder dashboard benchmark app.py serves
by default (see _dashboard_stats() in app.py).
"""
import json
from http.server import BaseHTTPRequestHandler

DEFAULT_DASHBOARD_STATS = {
    "throughput_per_min": 1240,
    "flagged_samples": 182,
    "total_samples": 5248,
    "accuracy": "96.4%",
    "false_positive": "1.8%",
    "latency_ms": 48,
    "blocked_naira": "₦8.7M",
    "discos_active": 11,
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
        payload = json.dumps(DEFAULT_DASHBOARD_STATS).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)
