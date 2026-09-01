// Vercel serverless endpoint: POST /api/predict
//
// Dependency-free port of the rule-based scorer in app.py. The real
// trained DNN/LSTM ensemble (model/*.h5) needs TensorFlow, which is far
// too large for a serverless function, so the hosted demo scores
// transactions with the same heuristic app.py falls back to when the ML
// models aren't available. Run app.py locally (see README) for real
// model inference.

function clamp(v, lo = 0, hi = 1) {
  return Math.max(lo, Math.min(hi, v));
}

function num(v, d = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

function ruleBased(amount, hour, velocity, isNew, isVpn, simSwap, numMeters, failLogins, distance, accountAge) {
  const night = hour < 6 || hour >= 22 ? 1 : 0;
  const base =
    clamp(Math.log1p(amount) / 13.0) * 0.24 +
    clamp(velocity / 20.0) * 0.16 +
    isVpn * 0.16 +
    simSwap * 0.14 +
    isNew * 0.1 +
    night * 0.08 +
    clamp(failLogins / 8.0) * 0.06 +
    clamp(numMeters / 10.0) * 0.04 +
    (1 - clamp(accountAge / 3650.0)) * 0.04 +
    clamp(distance / 500.0) * 0.02;
  const dnnP = clamp(base * 0.95 + 0.02);
  const lstmP = clamp(base * 0.9 + 0.04);
  const ensemble = dnnP * 0.6 + lstmP * 0.4;
  return { dnnP, lstmP, ensemble };
}

function predict(raw = {}) {
  const amount = num(raw.amount, 0);
  const hour = num(raw.hour, 0);
  const velocity = num(raw.velocity, 0);
  const isNew = num(raw.is_new_device, 0);
  const isVpn = num(raw.is_vpn, 0);
  const simSwap = num(raw.sim_swap, 0);
  const numMeters = num(raw.num_meters, 0);
  const failLogins = num(raw.fail_logins, 0);
  const distance = num(raw.distance, 0);
  const accountAge = num(raw.account_age, 0);

  const { dnnP, lstmP, ensemble } = ruleBased(
    amount, hour, velocity, isNew, isVpn, simSwap, numMeters, failLogins, distance, accountAge
  );

  const fraud = ensemble >= 0.5;
  const level = ensemble > 0.7 ? "HIGH" : ensemble > 0.4 ? "MEDIUM" : "LOW";
  const color = level === "HIGH" ? "#E24B4A" : level === "MEDIUM" ? "#BA7517" : "#639922";

  return {
    success: true,
    fraud,
    probability: Math.round(ensemble * 10000) / 100,
    dnn_prob: Math.round(dnnP * 10000) / 100,
    lstm_prob: Math.round(lstmP * 10000) / 100,
    risk_level: level,
    risk_color: color,
    verdict: fraud ? "FRAUDULENT" : "LEGITIMATE",
  };
}

module.exports = (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.status(200).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ success: false, error: "Method not allowed" });
    return;
  }

  try {
    let data = req.body;
    if (typeof data === "string") {
      data = data ? JSON.parse(data) : {};
    }
    if (!data || typeof data !== "object") data = {};
    res.status(200).json(predict(data));
  } catch (err) {
    res.status(400).json({ success: false, error: String((err && err.message) || err) });
  }
};
