// Vercel serverless endpoint: GET /api/live_feed?count=N
//
// Generates simulated transactions and scores them with the same
// dependency-free heuristic as api/predict.js, mirroring app.py's
// random_tx() for the local demo.

const DISCOS = ["AEDC", "EKEDC", "IKEDC", "EEDC", "PHEDC", "JEDC", "BEDC", "KAEDCO", "KEDCO", "YEDC", "IBEDC"];
const STATES = ["Abuja", "Lagos", "Rivers", "Kano", "Kaduna", "Enugu", "Imo", "Oyo", "Delta", "Edo", "Borno"];
const CHANNELS = ["web", "mobile_app", "ussd", "agent", "pos"];

function clamp(v, lo = 0, hi = 1) {
  return Math.max(lo, Math.min(hi, v));
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

function predict(raw) {
  const { amount, hour, velocity, is_new_device, is_vpn, sim_swap, num_meters, fail_logins, distance, account_age } = raw;
  const { dnnP, lstmP, ensemble } = ruleBased(
    amount, hour, velocity, is_new_device, is_vpn, sim_swap, num_meters, fail_logins, distance, account_age
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

function randInt(a, b) {
  return Math.floor(Math.random() * (b - a + 1)) + a;
}
function choice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}
function round1(v) {
  return Math.round(v * 10) / 10;
}

function randomTx() {
  const isFraud = Math.random() < 0.09;
  const disco = choice(DISCOS);
  const state = choice(STATES);
  const channel = choice(CHANNELS);
  let raw;
  let amount;

  if (isFraud) {
    amount = randInt(50000, 300000);
    raw = {
      amount,
      hour: choice([0, 1, 2, 3, 4, 5, 22, 23]),
      velocity: randInt(8, 25),
      is_new_device: choice([0, 1, 1]),
      is_vpn: choice([0, 1, 1]),
      sim_swap: choice([0, 1]),
      num_meters: randInt(3, 12),
      fail_logins: randInt(3, 8),
      distance: round1(Math.random() * (500 - 50) + 50),
      account_age: randInt(1, 60),
    };
  } else {
    amount = randInt(500, 25000);
    raw = {
      amount,
      hour: randInt(7, 21),
      velocity: randInt(1, 3),
      is_new_device: choice([0, 0, 0, 1]),
      is_vpn: choice([0, 0, 0, 1]),
      sim_swap: 0,
      num_meters: randInt(1, 2),
      fail_logins: randInt(0, 1),
      distance: round1(Math.random() * 15),
      account_age: randInt(100, 2000),
    };
  }

  const result = predict(raw);
  const id = "TXN" + Array.from({ length: 7 }, () => randInt(0, 9)).join("");
  const timestamp = new Date().toTimeString().slice(0, 8);

  return {
    id,
    disco,
    state,
    channel,
    amount: `NGN ${amount.toLocaleString("en-US")}`,
    timestamp,
    ...result,
  };
}

module.exports = (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.status(200).end();
    return;
  }

  const rawCount = (req.query && req.query.count) || "5";
  let count = parseInt(Array.isArray(rawCount) ? rawCount[0] : rawCount, 10);
  if (!Number.isFinite(count)) count = 5;
  count = Math.max(1, Math.min(50, count));

  const txs = Array.from({ length: count }, randomTx);
  res.status(200).json(txs);
};
