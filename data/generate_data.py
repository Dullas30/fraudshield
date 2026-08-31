"""
FraudShield NG - Synthetic Dataset Generator

Generates 50,000 realistic Nigerian electricity payment transactions
with about 9% fraud and saves them to data/transactions.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd


rng = np.random.default_rng(42)

DISCOS = ["AEDC", "EKEDC", "IKEDC", "EEDC", "PHEDC", "JEDC", "BEDC", "KAEDCO", "KEDCO", "YEDC", "IBEDC"]
STATES = ["Abuja", "Lagos", "Rivers", "Kano", "Kaduna", "Enugu", "Imo", "Oyo", "Delta", "Edo", "Borno"]
CHANNELS = ["web", "mobile_app", "ussd", "agent", "pos"]

N_TOTAL = 50_000
FRAUD_RATE = 0.09
N_FRAUD = int(N_TOTAL * FRAUD_RATE)
N_LEGIT = N_TOTAL - N_FRAUD


def _ints(lo, hi, n):
    return rng.integers(lo, hi + 1, n)


def _floats(lo, hi, n):
    return np.round(rng.uniform(lo, hi, n), 1)


def _choice(pool, n, p=None):
    return rng.choice(pool, n, p=p)


def _generate_fraud(n):
    odd_hours = list(range(0, 6)) + list(range(22, 24))

    return pd.DataFrame(
        {
            "amount": _ints(50_000, 300_000, n),
            "hour": _choice(odd_hours, n),
            "velocity": _ints(8, 25, n),
            "is_new_device": _choice([0, 1, 1], n),
            "is_vpn": _choice([0, 1, 1], n),
            "sim_swap": _choice([0, 1], n),
            "num_meters": _ints(3, 12, n),
            "fail_logins": _ints(3, 8, n),
            "distance": _floats(50.0, 500.0, n),
            "account_age": _ints(1, 60, n),
            "disco": _choice(DISCOS, n),
            "state": _choice(STATES, n),
            "channel": _choice(CHANNELS, n),
            "is_fraud": np.ones(n, dtype=int),
        }
    )


def _generate_legit(n):
    channel_probs = [0.35, 0.30, 0.15, 0.10, 0.10]

    return pd.DataFrame(
        {
            "amount": _ints(500, 25_000, n),
            "hour": _ints(7, 21, n),
            "velocity": _ints(1, 3, n),
            "is_new_device": _choice([0, 0, 0, 1], n),
            "is_vpn": _choice([0] * 9 + [1], n),
            "sim_swap": np.zeros(n, dtype=int),
            "num_meters": _ints(1, 2, n),
            "fail_logins": _ints(0, 1, n),
            "distance": _floats(0.0, 15.0, n),
            "account_age": _ints(100, 2_000, n),
            "disco": _choice(DISCOS, n),
            "state": _choice(STATES, n),
            "channel": _choice(CHANNELS, n, p=channel_probs),
            "is_fraud": np.zeros(n, dtype=int),
        }
    )


def main():
    print("\nFraudShield NG - Dataset Generator")
    print("=" * 46)
    print(f"  Total transactions : {N_TOTAL:,}")
    print(f"  Fraudulent         : {N_FRAUD:,}  ({FRAUD_RATE * 100:.0f} %)")
    print(f"  Legitimate         : {N_LEGIT:,}")
    print()

    df = (
        pd.concat([_generate_fraud(N_FRAUD), _generate_legit(N_LEGIT)], ignore_index=True)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )
    df.insert(0, "txn_id", [f"TXN{str(i).zfill(7)}" for i in range(len(df))])

    out_path = Path(__file__).resolve().parent / "transactions.csv"
    df.to_csv(out_path, index=False)

    print(f"  Saved -> {out_path}")
    print()
    print("  Label distribution:")
    vc = df["is_fraud"].value_counts().rename({0: "Legitimate", 1: "Fraud"})
    for label, cnt in vc.items():
        print(f"    {label:<12} {cnt:>6,}  ({cnt / len(df) * 100:.1f} %)")
    print()
    print("  Mean values by label:")
    means = df.groupby("is_fraud")[["amount", "hour", "velocity", "account_age", "distance"]].mean().rename(
        index={0: "Legit", 1: "Fraud"}
    )
    print(means.to_string())
    print()
    print("  Done. Next step: python train.py\n")


if __name__ == "__main__":
    main()
