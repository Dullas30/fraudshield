import os
import warnings
import sys
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

if sys.version_info < (3, 10) or sys.version_info >= (3, 14):
    raise RuntimeError(
        "This training setup expects Python 3.10-3.13. "
        "Python 3.11 is the safest choice for TensorFlow 2.21."
    )

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight

import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import (
    BatchNormalization,
    Dense,
    Dropout,
    LSTM,
    Reshape,
)
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "transactions.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_DIR.mkdir(exist_ok=True)
NUMERIC_COLS = [
    "amount", "hour", "velocity", "is_new_device", "is_vpn",
    "sim_swap", "num_meters", "fail_logins", "distance", "account_age",
]
CAT_COLS = ["disco", "state", "channel"]
TARGET   = "is_fraud"
def _sep(title: str = "") -> None:
    w = 54
    if title:
        pad = (w - len(title) - 2) // 2
        print("\n" + "─" * pad + f" {title} " + "─" * (w - pad - len(title) - 2))
    else:
        print("\n" + "─" * w)
def load_data() -> pd.DataFrame:
    _sep("Loading data")
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"\n  Dataset not found at:\n    {DATA_PATH}\n"
            "  Run:  python data/generate_data.py  first.\n"
        )
    df = pd.read_csv(DATA_PATH)
    n_fraud = int(df[TARGET].sum())
    n_legit = len(df) - n_fraud
    print(f"  Rows    : {len(df):,}")
    print(f"  Fraud   : {n_fraud:,}  ({n_fraud / len(df) * 100:.1f} %)")
    print(f"  Legit   : {n_legit:,}")
    return df
def build_preprocessor() -> ColumnTransformer:
    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_COLS),
            ("cat", ohe,             CAT_COLS),
        ],
        remainder="drop",
    )


def preprocess(df: pd.DataFrame):
    _sep("Preprocessing")
    X_raw = df[NUMERIC_COLS + CAT_COLS]
    y     = df[TARGET].values

    prep = build_preprocessor()
    X    = prep.fit_transform(X_raw)
    print(f"  Input features  : {len(NUMERIC_COLS)} numeric + {len(CAT_COLS)} categorical")
    print(f"  After encoding  : {X.shape[1]} total features")
    print(f"  Feature matrix  : {X.shape}")
    return X, y, prep
def get_class_weights(y: np.ndarray) -> dict:
    classes = np.unique(y)
    weights = compute_class_weight("balanced", classes=classes, y=y)
    cw = {int(c): float(w) for c, w in zip(classes, weights)}
    print(f"  Class weights   : {cw}")
    return cw
def build_dnn(input_dim: int) -> Sequential:
    model = Sequential(
        [
            Dense(256, activation="relu", input_shape=(input_dim,)),
            BatchNormalization(),
            Dropout(0.3),

            Dense(128, activation="relu"),
            BatchNormalization(),
            Dropout(0.3),

            Dense(64, activation="relu"),
            BatchNormalization(),
            Dropout(0.2),

            Dense(32, activation="relu"),
            Dense(1,  activation="sigmoid"),
        ],
        name="FraudShield_DNN",
    )
    model.compile(
        optimizer=Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
    )
    return model


def build_lstm(input_dim: int) -> Sequential:
    model = Sequential(
        [
            Reshape((input_dim, 1), input_shape=(input_dim,)),
            LSTM(64, return_sequences=True),
            LSTM(32),
            Dense(16, activation="relu"),
            Dropout(0.2),
            Dense(1,  activation="sigmoid"),
        ],
        name="FraudShield_LSTM",
    )
    model.compile(
        optimizer=Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
    )
    return model
_CALLBACKS = [
    EarlyStopping(
        monitor="val_loss", patience=5,
        restore_best_weights=True, verbose=1,
    ),
    ReduceLROnPlateau(
        monitor="val_loss", factor=0.5,
        patience=3, min_lr=1e-5, verbose=1,
    ),
]
def train_model(model: Sequential, X_tr, y_tr, class_weights: dict):
    return model.fit(
        X_tr, y_tr,
        validation_split=0.15,
        epochs=50,
        batch_size=512,
        class_weight=class_weights,
        callbacks=_CALLBACKS,
        verbose=1,
    )
def evaluate(name: str, y_true, y_prob, threshold: float = 0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)

    acc  = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec  = recall_score(y_true, y_pred, zero_division=0)
    f1   = f1_score(y_true, y_pred, zero_division=0)
    auc  = roc_auc_score(y_true, y_prob)
    cm   = confusion_matrix(y_true, y_pred)

    _sep(name)
    print(f"  Accuracy   : {acc:.4f}  ({acc * 100:.2f} %)")
    print(f"  Precision  : {prec:.4f}")
    print(f"  Recall     : {rec:.4f}")
    print(f"  F1 Score   : {f1:.4f}")
    print(f"  AUC-ROC    : {auc:.4f}")
    print()
    print("  Confusion Matrix (rows = actual, cols = predicted):")
    print(f"                Predicted 0   Predicted 1")
    print(f"  Actual 0    {cm[0, 0]:>12,}  {cm[0, 1]:>11,}")
    print(f"  Actual 1    {cm[1, 0]:>12,}  {cm[1, 1]:>11,}")
    print()
    print("  Full Classification Report:")
    print(
        classification_report(
            y_true, y_pred,
            target_names=["Legitimate", "Fraud"],
        )
    )
    return {
        "accuracy": acc, "precision": prec,
        "recall": rec, "f1": f1, "auc": auc,
    }
def main():
    print("\nFraudShield – Model Training")
    print("=" * 54)

    df         = load_data()
    X, y, prep = preprocess(df)

    _sep("Train / test split")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
    print(f"  Train : {len(X_tr):,}   Test : {len(X_te):,}")
    cw        = get_class_weights(y_tr)
    input_dim = X.shape[1]
    print(f"  Input dimension : {input_dim}")

    _sep("Training DNN")
    dnn = build_dnn(input_dim)
    dnn.summary()
    train_model(dnn, X_tr, y_tr, cw)

    dnn_prob = dnn.predict(X_te, verbose=0).flatten()
    dnn_m    = evaluate("DNN — Test Results", y_te, dnn_prob)

    dnn_path = str(MODEL_DIR / "dnn.h5")
    dnn.save(dnn_path, save_format="h5")
    print(f"  Saved  →  {dnn_path}")

    _sep("Training LSTM")
    lstm = build_lstm(input_dim)
    lstm.summary()
    train_model(lstm, X_tr, y_tr, cw)

    lstm_prob = lstm.predict(X_te, verbose=0).flatten()
    lstm_m    = evaluate("LSTM — Test Results", y_te, lstm_prob)

    lstm_path = str(MODEL_DIR / "lstm.h5")
    lstm.save(lstm_path, save_format="h5")
    print(f"  Saved  →  {lstm_path}")

    ens_prob = 0.60 * dnn_prob + 0.40 * lstm_prob
    ens_m    = evaluate("Ensemble 60 % DNN + 40 % LSTM", y_te, ens_prob)

    prep_path = str(MODEL_DIR / "preprocessor.pkl")
    joblib.dump(
        {
            "preprocessor":         prep,
            "numeric_features":     NUMERIC_COLS,
            "categorical_features": CAT_COLS,
            "input_dim":            input_dim,
        },
        prep_path,
    )
    print(f"\n  Saved  →  {prep_path}")

    _sep("Final Summary")
    header = f"  {'Model':<35} {'AUC-ROC':>8}  {'F1':>8}  {'Recall':>8}  {'Prec':>8}"
    print(header)
    print("  " + "─" * (len(header) - 2))
    rows = [
        ("DNN",                        dnn_m),
        ("LSTM",                       lstm_m),
        ("Ensemble (60% DNN + 40% LSTM)", ens_m),
    ]
    for lbl, m in rows:
        print(
            f"  {lbl:<35} {m['auc']:>8.4f}  "
            f"{m['f1']:>8.4f}  {m['recall']:>8.4f}  {m['precision']:>8.4f}"
        )

    print()
    print("  model/ contents:")
    for f in sorted(MODEL_DIR.iterdir()):
        size_kb = f.stat().st_size / 1024
        print(f"    {f.name:<25}  {size_kb:>8.1f} KB")

    print()
    print("  Next step:  python app.py\n")


if __name__ == "__main__":
    main()
