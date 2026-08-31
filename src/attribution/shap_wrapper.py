import shap
import pickle
from typing import Dict, List, Any

class ShapAttributor:
    def __init__(self, model_path: str, background_data_path: str):
        self.model = pickle.load(open(model_path, 'rb'))
        self.background = pickle.load(open(background_data_path, 'rb'))
        self.explainer = shap.TreeExplainer(self.model, self.background)
    
    def get_attributions(self, features: Dict[str, float]) -> List[Dict[str, Any]]:
        # Returns: [{"feature": "amount", "value": 0.31}, ...]
        raise NotImplementedError("Implement in Sprint 2")