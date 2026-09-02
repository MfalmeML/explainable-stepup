"""
One-time setup script: trains a tabular fraud-risk model and saves both the
model and a SHAP background sample to disk, matching the paths expected by
config/production_config.json (model_path, background_path).

Nothing in this repo currently creates these two files -- init_data.py only
populates the outcome store with sample decision records, it never trains or
exports a model. Run this once before `python run.py <config> process`.

Usage:
    python setup_model.py
"""
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "models/tabular_model.pkl"
BACKGROUND_PATH = "models/background_data.pkl"

# Matches the 4 features run.py's `process` command sends as transaction_features.
FEATURE_NAMES = ["amount", "device_count", "age_days", "velocity_1h"]


def build_training_data(n_samples: int = 2000, seed: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)

    amount = rng.exponential(scale=200, size=n_samples)
    device_count = rng.poisson(lam=2, size=n_samples)
    age_days = rng.exponential(scale=180, size=n_samples)
    velocity_1h = rng.poisson(lam=1.5, size=n_samples)

    X = pd.DataFrame({
        "amount": amount,
        "device_count": device_count,
        "age_days": age_days,
        "velocity_1h": velocity_1h,
    })

    # Synthetic risk signal: large amount + many linked devices + high velocity
    # + a young account all push risk up. This is a placeholder model for
    # local development/demo purposes, not a real fraud model.
    risk_score = (
        0.004 * amount
        + 0.6 * device_count
        + 0.5 * velocity_1h
        - 0.01 * age_days
        + rng.normal(0, 1, size=n_samples)
    )
    y = (risk_score > risk_score.mean()).astype(int)

    return X, pd.Series(y)


def main():
    os.makedirs("models", exist_ok=True)

    X, y = build_training_data()

    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X, y)

    background = X.sample(n=50, random_state=42).reset_index(drop=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(BACKGROUND_PATH, "wb") as f:
        pickle.dump(background, f)

    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved background data ({len(background)} rows) to {BACKGROUND_PATH}")
    print(f"Features: {FEATURE_NAMES}")


if __name__ == "__main__":
    main()