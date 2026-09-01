import shap
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any

class ShapAttributor:
    def __init__(self, model_path: str, background_data_path: str):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(background_data_path, 'rb') as f:
            self.background = pickle.load(f)
        self.explainer = shap.TreeExplainer(self.model, self.background)
        self.feature_names = list(self.background.columns) if hasattr(self.background, 'columns') else [f"feature_{i}" for i in range(self.background.shape[1])]
    
    def get_attributions(self, features: Dict[str, float]) -> List[Dict[str, Any]]:
        # Convert dict to DataFrame with correct column order, defaulting any
        # missing feature to 0.0 instead of raising a KeyError
        row = {name: features.get(name, 0.0) for name in self.feature_names}
        input_df = pd.DataFrame([row])[self.feature_names]
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(input_df)
        
        # Normalize to a 1D array of per-feature SHAP values for this single
        # sample, on the positive class. Handle both SHAP output shapes:
        #   - older shap: list of (n_samples, n_features) arrays, one per class
        #   - newer shap: single ndarray shaped (n_samples, n_features, n_classes)
        if isinstance(shap_values, list):
            # Prefer the positive class (index 1) if this is binary output
            class_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            sample_values = np.asarray(class_values[0])
        else:
            arr = np.asarray(shap_values[0])
            if arr.ndim == 2:
                # (n_features, n_classes) -> take positive class column
                sample_values = arr[:, 1] if arr.shape[1] > 1 else arr[:, 0]
            else:
                sample_values = arr
        
        # Convert to list of feature contributions
        attributions = []
        for idx, feature_name in enumerate(self.feature_names):
            value = float(features.get(feature_name, 0.0))
            shap_value = float(sample_values[idx])
            
            # Only include features with non-zero contribution
            if abs(shap_value) > 0.001:
                attributions.append({
                    "feature": feature_name,
                    "value": value,
                    "shap_value": shap_value,
                    "source": "tabular",
                    "severity_weight": abs(shap_value)  # Use absolute SHAP as weight
                })
        
        # Sort by absolute SHAP value descending
        attributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return attributions