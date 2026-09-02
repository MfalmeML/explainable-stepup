import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import os
import sys

def generate_models(output_dir: str = "models"):
    """Generate production model files."""
    os.makedirs(output_dir, exist_ok=True)
    
    np.random.seed(42)
    
    # Generate training data
    n_samples = 10000
    X = pd.DataFrame({
        'amount': np.random.randn(n_samples) * 100 + 500,
        'device_count': np.random.poisson(2, n_samples),
        'age_days': np.random.exponential(365, n_samples),
        'velocity_1h': np.random.poisson(1, n_samples),
        'velocity_24h': np.random.poisson(10, n_samples),
        'ip_match': np.random.binomial(1, 0.85, n_samples),
        'country_match': np.random.binomial(1, 0.9, n_samples),
        'session_duration': np.random.exponential(600, n_samples),
        'payment_method_age': np.random.exponential(365, n_samples),
        'failed_attempts': np.random.poisson(0.2, n_samples)
    })
    
    # Synthetic fraud label (10% fraud rate)
    fraud_prob = (
        0.3 * (X['amount'] > 800) +
        0.4 * (X['device_count'] > 5) +
        0.3 * (X['age_days'] < 30) +
        0.2 * (X['velocity_1h'] > 5) +
        0.1 * (X['ip_match'] == 0)
    )
    y = (np.random.rand(n_samples) < fraud_prob).astype(int)
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)
    
    # Background data for SHAP (sample 100 rows)
    background = X.sample(100, random_state=42)
    
    # Save
    model_path = os.path.join(output_dir, "tabular_model.pkl")
    background_path = os.path.join(output_dir, "background_data.pkl")
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(background_path, 'wb') as f:
        pickle.dump(background, f)
    
    print(f"Model saved to: {model_path}")
    print(f"Background data saved to: {background_path}")
    print(f"Feature names: {list(X.columns)}")
    
    return model_path, background_path

if __name__ == "__main__":
    generate_models()