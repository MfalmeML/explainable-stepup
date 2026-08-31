import shap
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any

class ShapAttributor:
    def __init__(self, model_path: str, background_data_path: str):
        self.model = pickle.load(open(model_path, 'rb'))
        self.background = pickle.load(open(background_data_path, 'rb'))
        self.explainer = shap.TreeExplainer(self.model, self.background)
        self.feature_names = list(self.background.columns) if hasattr(self.background, 'columns') else [f"feature_{i}" for i in range(self.background.shape[1])]
    
    def get_attributions(self, features: Dict[str, float]) -> List[Dict[str, Any]]:
        # Convert dict to DataFrame with correct column order
        input_df = pd.DataFrame([features])[self.feature_names]
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(input_df)
        
        # Handle multi-class output (take first class if binary classification)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Convert to list of feature contributions
        attributions = []
        for idx, feature_name in enumerate(self.feature_names):
            value = float(features.get(feature_name, 0.0))
            shap_value = float(shap_values[0][idx])
            
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