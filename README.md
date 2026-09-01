# FraudShield

FraudShield is a demo for detecting fraud in Nigerian electricity prepaid payment transactions.
It uses synthetic data, trains a real DNN and LSTM, combines them in a 60/40 ensemble, and serves results through Python's standard library HTTP server.

There are two ways to run it:

- **Live/hosted (Vercel)** — `index.html` is served as a static page, and `/api/predict`, `/api/live_feed`, and `/api/stats` are Vercel **Node.js** serverless functions (`api/*.js`) that use the same rule-based scoring heuristic `app.py` falls back to. This keeps the deployment tiny and fast — no TensorFlow, no model files, no cold starts, and no Python-runtime entrypoint ambiguity. The frontend also has a client-side JS fallback (`clientPredict` in `index.html`) that runs the same math if a request ever fails, so the demo never shows a blank result.
- **Local full stack** — `python app.py` serves `index.html` and loads the real trained DNN/LSTM ensemble from `model/` for genuine ML inference (falling back to the same heuristic if the models or their dependencies aren't available).

## Deploying to GitHub + Vercel

1. Push this repo to GitHub:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. Go to [vercel.com/new](https://vercel.com/new), import the GitHub repo, and click **Deploy** — no configuration needed.

   - Vercel auto-detects `index.html` as the static site and the files in `api/*.js` as Node.js serverless functions (zero-config, no `vercel.json` needed).
   - The heavier local-only files (`app.py`, `train.py`, `data/`, `model/`, etc.) are excluded from the deployment via `.vercelignore`, so the deployed site is only a few MB.
   - Once deployed, the site is fully interactive: the manual form, scenario buttons, live feed, and dashboard stats all hit the `/api/*` functions for real (simulated) responses.

## Local Setup (real ML models)

Recommended environment:

- Python 3.11
- Windows, macOS, or Linux
- A virtual environment

1. Install dependencies

```bash
pip install -r requirements-local.txt
```

If you're on Python 3.14, install Python 3.11 or 3.12 first. TensorFlow 2.21 supports Python 3.10 through 3.13, so 3.11 is the safest option for this project.

2. Generate the synthetic dataset

```bash
python data/generate_data.py
```

This creates `data/transactions.csv` with 50,000 rows and about 9% fraud.

3. Train the models

```bash
python train.py
```

This trains:

- a DNN with BatchNormalization and Dropout
- an LSTM that treats the tabular features as a short sequence
- a 60% DNN + 40% LSTM ensemble

It saves:

```text
model/dnn.h5
model/lstm.h5
model/preprocessor.pkl
```

4. Start the local server

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

## Project Files

- `data/generate_data.py` - creates the synthetic dataset
- `train.py` - trains and evaluates the DNN/LSTM ensemble
- `app.py` - standard-library HTTP server and prediction endpoint
- `requirements.txt` - Python dependencies
- `index.html` - frontend UI already provided in the project

## Dataset Design

The synthetic dataset includes:

- `amount` - payment amount in NGN
- `hour` - transaction hour
- `velocity` - transactions per hour on the same account
- `is_new_device` - whether the device is new
- `is_vpn` - VPN or proxy usage
- `sim_swap` - recent SIM swap activity
- `num_meters` - number of meter IDs involved
- `fail_logins` - failed login count
- `distance` - distance between device location and meter location
- `account_age` - account age in days
- `disco` - one of 11 Nigerian DisCos
- `state` - one of 11 Nigerian states
- `channel` - web, mobile_app, ussd, agent, or pos

### Fraud patterns

Fraudulent transactions are generated with believable high-risk signals:

- high amounts, usually NGN 50,000 to NGN 300,000
- odd hours, usually 10pm to 6am
- high velocity
- VPN active
- SIM swap presence
- new device usage
- short account age
- larger meter counts
- higher failed logins
- larger distance from the registered location

### Legitimate patterns

Legitimate transactions are generated with:

- lower amounts, usually NGN 500 to NGN 25,000
- daytime activity
- low velocity
- established account age
- fewer meters
- few failed logins
- short distance

## Model Architecture

### DNN

The deep neural network uses:

- Dense(256, ReLU)
- BatchNormalization
- Dropout(0.3)
- Dense(128, ReLU)
- BatchNormalization
- Dropout(0.3)
- Dense(64, ReLU)
- BatchNormalization
- Dropout(0.2)
- Dense(32, ReLU)
- Dense(1, sigmoid)

It learns nonlinear combinations of the tabular features.

### LSTM

The LSTM treats the preprocessed feature vector as a sequence:

- Reshape to `(n_features, 1)`
- LSTM(64, return_sequences=True)
- LSTM(32)
- Dense(16, ReLU)
- Dropout(0.2)
- Dense(1, sigmoid)

This gives a second view of the same transaction data so the ensemble is more robust.

### Ensemble

The final fraud probability is:

```text
P_ensemble = 0.60 * P_DNN + 0.40 * P_LSTM
```

The DNN gets the heavier weight because tabular fraud data usually favors feed-forward models.

## Evaluation Metrics

`train.py` prints:

- Accuracy
- Precision
- Recall
- F1 score
- AUC-ROC
- Confusion matrix
- Full classification report

## What You Can Honestly Report

Because the dataset is synthetic and intentionally separable, the scores will usually be high.
For a realistic final-year writeup, a safe expectation is:

- DNN accuracy: about 97% to 98%
- DNN AUC-ROC: about 0.99
- LSTM accuracy: about 96% to 97%
- LSTM AUC-ROC: about 0.98 to 0.99
- Ensemble accuracy: about 97% to 98%
- Ensemble AUC-ROC: about 0.99

The honest caveat to include is:

- the dataset is synthetic
- the fraud patterns are deliberately clear
- real-world fraud performance will be lower and less stable

## Windows Notes

- This project is designed to run on Python 3.8+ on Windows
- If the newest TensorFlow release gives installation trouble, use the pinned version in `requirements.txt`
