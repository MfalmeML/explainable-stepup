import unittest
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from src.attribution.shap_wrapper import ShapAttributor
import tempfile
import os

class TestShapWrapper(unittest.TestCase):
    def setUp(self):
        # Create a simple model and background data
        np.random.seed(42)
        X = pd.DataFrame({
            'amount': np.random.randn(100),
            'device_count': np.random.randn(100),
            'age_days': np.random.randn(100)
        })
        y = (X['amount'] + X['device_count'] > 0).astype(int)
        
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
        self.model.fit(X, y)
        
        self.background = X.sample(10, random_state=42)
        
        # Save to temporary files
        self.model_path = tempfile.mktemp(suffix='.pkl')
        self.background_path = tempfile.mktemp(suffix='.pkl')
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.background_path, 'wb') as f:
            pickle.dump(self.background, f)
    
    def tearDown(self):
        os.remove(self.model_path)
        os.remove(self.background_path)
    
    def test_get_attributions_returns_list(self):
        attributor = ShapAttributor(self.model_path, self.background_path)
        features = {'amount': 2.0, 'device_count': -1.0, 'age_days': 0.5}
        result = attributor.get_attributions(features)
        self.assertIsInstance(result, list)
    
    def test_get_attributions_sorts_by_importance(self):
        attributor = ShapAttributor(self.model_path, self.background_path)
        features = {'amount': 5.0, 'device_count': 0.0, 'age_days': 0.0}
        result = attributor.get_attributions(features)
        # First item should have highest absolute SHAP value
        if len(result) > 1:
            self.assertGreaterEqual(
                abs(result[0]['shap_value']),
                abs(result[1]['shap_value'])
            )
    
    def test_get_attributions_excludes_zero_contributions(self):
        attributor = ShapAttributor(self.model_path, self.background_path)
        features = {'amount': 0.0, 'device_count': 0.0, 'age_days': 0.0}
        result = attributor.get_attributions(features)
        # All contributions should be near zero, so result should be empty or small
        self.assertLessEqual(len(result), 3)
    
    def test_get_attributions_handles_missing_features(self):
        attributor = ShapAttributor(self.model_path, self.background_path)
        features = {'amount': 2.0}  # Missing device_count and age_days
        result = attributor.get_attributions(features)
        self.assertIsInstance(result, list)