// Vercel serverless endpoint: GET /api/stats
//
// Returns the same realistic placeholder dashboard benchmark app.py
// serves by default (see _dashboard_stats() in app.py).

const DEFAULT_DASHBOARD_STATS = {
  throughput_per_min: 1240,
  flagged_samples: 182,
  total_samples: 5248,
  accuracy: "96.4%",
  false_positive: "1.8%",
  latency_ms: 48,
  blocked_naira: "₦8.7M",
  discos_active: 11,
};

module.exports = (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.status(200).end();
    return;
  }

  res.status(200).json(DEFAULT_DASHBOARD_STATS);
};
