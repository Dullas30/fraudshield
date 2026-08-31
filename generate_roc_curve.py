"""
FraudShield – ROC Curve Generator
===================================
Run this script from inside your Fraudshield folder:

    python generate_roc_curve.py

It will:
  1. Re-load your saved models (model/dnn.h5 and model/lstm.h5)
  2. Re-generate the same test split you used during training
  3. Plot ROC curves for DNN, LSTM, and Ensemble on one chart
  4. Save the image as  roc_curve.png  in the same folder

Requirements: same as your project (tensorflow, scikit-learn, matplotlib)
"""

import warnings
warnings.filterwarnings("ignore")

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
import joblib
import tensorflow as tf

# ── Paths ─────────────────────────────────────────────────────────────
BASE        = Path(__file__).resolve().parent
DATA_PATH   = BASE / "data" / "transactions.csv"
MODEL_DIR   = BASE / "model"
DNN_PATH    = MODEL_DIR / "dnn.h5"
LSTM_PATH   = MODEL_DIR / "lstm.h5"
PREP_PATH   = MODEL_DIR / "preprocessor.pkl"
OUT_PATH    = BASE / "roc_curve.png"

# ── Feature columns (must match train.py exactly) ─────────────────────
NUMERIC_COLS = [
    "amount", "hour", "velocity", "is_new_device",
    "is_vpn", "sim_swap", "num_meters", "fail_logins",
    "distance", "account_age",
]
CAT_COLS = ["disco", "state", "channel"]
TARGET   = "is_fraud"

# ── Ensemble weights ──────────────────────────────────────────────────
DNN_W  = 0.60
LSTM_W = 0.40

# ─────────────────────────────────────────────────────────────────────
print("\n── FraudShield ROC Curve Generator ──\n")

# 1. Load dataset
if not DATA_PATH.exists():
    sys.exit(f"ERROR: Dataset not found at {DATA_PATH}\n"
             f"  Run:  python data/generate_data.py  first.")

print(f"Loading dataset from {DATA_PATH} ...")
df = pd.read_csv(DATA_PATH)
print(f"  Rows: {len(df):,}  |  Fraud: {df[TARGET].sum():,} ({df[TARGET].mean()*100:.1f}%)")

# 2. Load preprocessor (or rebuild it on the training split)
X_raw = df[NUMERIC_COLS + CAT_COLS]
y     = df[TARGET].values

if PREP_PATH.exists():
    print(f"Loading preprocessor from {PREP_PATH} ...")
    prep_bundle = joblib.load(PREP_PATH)
    # train.py saves a dictionary with the fitted preprocessor under
    # the "preprocessor" key, so handle both the dict and direct-object cases.
    prep = prep_bundle["preprocessor"] if isinstance(prep_bundle, dict) else prep_bundle
    X    = prep.transform(X_raw)
else:
    print("Preprocessor not found – rebuilding from training split ...")
    ohe  = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    prep = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_COLS),
        ("cat", ohe,             CAT_COLS),
    ])
    X_tr_raw, _, _, _ = train_test_split(
        X_raw, y, test_size=0.20, random_state=42, stratify=y)
    prep.fit(X_tr_raw)   # fit on training rows only
    X = prep.transform(X_raw)

# 3. Reproduce the exact same test split as train.py
print("Reproducing test split (random_state=42, stratified) ...")
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y)
print(f"  Test set : {len(y_te):,} instances  "
      f"({int(y_te.sum())} fraud / {int((1-y_te).sum())} legitimate)")

# 4. Load models
print(f"\nLoading DNN  from {DNN_PATH} ...")
dnn  = tf.keras.models.load_model(str(DNN_PATH))

print(f"Loading LSTM from {LSTM_PATH} ...")
lstm = tf.keras.models.load_model(str(LSTM_PATH))

# 5. Get probability predictions
print("\nRunning predictions on test set ...")
p_dnn  = dnn.predict(X_te,  verbose=0).ravel()
p_lstm = lstm.predict(X_te, verbose=0).ravel()
p_ens  = DNN_W * p_dnn + LSTM_W * p_lstm

# 6. Compute ROC curves
fpr_dnn,  tpr_dnn,  _ = roc_curve(y_te, p_dnn)
fpr_lstm, tpr_lstm, _ = roc_curve(y_te, p_lstm)
fpr_ens,  tpr_ens,  _ = roc_curve(y_te, p_ens)

auc_dnn  = auc(fpr_dnn,  tpr_dnn)
auc_lstm = auc(fpr_lstm, tpr_lstm)
auc_ens  = auc(fpr_ens,  tpr_ens)

print(f"\n  AUC-ROC  DNN      : {auc_dnn:.4f}")
print(f"  AUC-ROC  LSTM     : {auc_lstm:.4f}")
print(f"  AUC-ROC  Ensemble : {auc_ens:.4f}")

# 7. Plot
fig, ax = plt.subplots(figsize=(7, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# Random baseline
ax.plot([0, 1], [0, 1], linestyle="--", linewidth=1.2,
        color="#AAAAAA", label="Random Classifier (AUC = 0.50)")

# Model curves
ax.plot(fpr_dnn,  tpr_dnn,  linewidth=2.2,
        color="#1F77B4", label=f"Deep Neural Network  (AUC = {auc_dnn:.4f})")
ax.plot(fpr_lstm, tpr_lstm, linewidth=2.2, linestyle="-.",
        color="#FF7F0E", label=f"LSTM                 (AUC = {auc_lstm:.4f})")
ax.plot(fpr_ens,  tpr_ens,  linewidth=2.5, linestyle=":",
        color="#2CA02C", label=f"Ensemble (60% DNN + 40% LSTM)  (AUC = {auc_ens:.4f})")

# Formatting
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.02])
ax.set_xlabel("False Positive Rate (1 – Specificity)", fontsize=11)
ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11)
ax.set_title(
    "ROC Curves — FraudShield Fraud Detection System\n"
    "DNN, LSTM, and Ensemble Classifiers (Test Set, n = 10,000)",
    fontsize=11, fontweight="bold", pad=14
)
ax.legend(loc="lower right", fontsize=9.5, framealpha=0.9)
ax.grid(True, linestyle="--", alpha=0.4)
ax.tick_params(labelsize=10)

plt.tight_layout()
plt.savefig(str(OUT_PATH), dpi=200, bbox_inches="tight")
plt.close()

print(f"\n✓  ROC curve saved → {OUT_PATH}")
print("  Screenshot that file and send it to insert into Chapter 4.\n")
