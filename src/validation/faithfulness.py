import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class FaithfulnessTester:
    def __init__(self, store_path: str, model_path: str, background_path: str):
        self.store_path = store_path
        self.model_path = model_path
        self.background_path = background_path
        self._load_model()
    
    def _load_model(self):
        import pickle
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(self.background_path, 'rb') as f:
            self.background = pickle.load(f)
        self.feature_names = list(self.background.columns)
    
    def test_explanation_faithfulness(
        self,
        transaction_id: str,
        features: Dict[str, float],
        reason: Dict[str, Any],
        perturbation_scale: float = 0.1
    ) -> Dict:
        """Test if a stated reason actually affects the model prediction."""
        # Get feature name from reason
        feature_name = reason.get('feature', reason.get('text', ''))
        
        # Parse feature name from text if needed
        if feature_name in features:
            pass
        elif 'amount' in feature_name.lower():
            feature_name = 'amount'
        elif 'device' in feature_name.lower():
            feature_name = 'device_count'
        elif 'age' in feature_name.lower():
            feature_name = 'age_days'
        else:
            return {
                "transaction_id": transaction_id,
                "reason_text": reason.get('text', ''),
                "passed": None,
                "error": "Could not map reason to feature"
            }
        
        if feature_name not in features:
            return {
                "transaction_id": transaction_id,
                "reason_text": reason.get('text', ''),
                "passed": None,
                "error": f"Feature {feature_name} not in features"
            }
        
        # Baseline prediction
        input_df = pd.DataFrame([features])[self.feature_names]
        baseline_pred = self.model.predict_proba(input_df)[0][1]
        
        # Perturb the feature
        perturbed_features = features.copy()
        original_value = perturbed_features[feature_name]
        
        # Apply perturbation
        if isinstance(original_value, (int, float)):
            perturbed_value = original_value * (1 + perturbation_scale * np.random.choice([-1, 1]))
            perturbed_features[feature_name] = perturbed_value
        else:
            return {
                "transaction_id": transaction_id,
                "reason_text": reason.get('text', ''),
                "passed": None,
                "error": "Feature is not numeric"
            }
        
        # New prediction
        perturbed_df = pd.DataFrame([perturbed_features])[self.feature_names]
        perturbed_pred = self.model.predict_proba(perturbed_df)[0][1]
        
        # Check if prediction changed meaningfully
        pred_change = abs(perturbed_pred - baseline_pred)
        passed = pred_change > 0.01
        
        return {
            "transaction_id": transaction_id,
            "reason_text": reason.get('text', ''),
            "feature": feature_name,
            "original_value": original_value,
            "perturbed_value": perturbed_value,
            "baseline_prediction": float(baseline_pred),
            "perturbed_prediction": float(perturbed_pred),
            "prediction_change": float(pred_change),
            "passed": passed,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def run_faithfulness_checks(
        self,
        sample_size: int = 10,
        min_reasons_per_case: int = 1
    ) -> Dict:
        """Run faithfulness checks on a sample of stored cases."""
        with open(self.store_path, 'r') as f:
            store = json.load(f)
        
        # Find cases with explanations
        cases_with_reasons = []
        for tx_id, data in store.items():
            if 'reasons' in data and data['reasons']:
                if 'transaction_features' in data:
                    cases_with_reasons.append((tx_id, data))
        
        if not cases_with_reasons:
            return {"error": "No cases with reasons found"}
        
        # Sample cases
        import random
        sampled = random.sample(cases_with_reasons, min(sample_size, len(cases_with_reasons)))
        
        results = []
        for tx_id, data in sampled:
            features = data.get('transaction_features', {})
            if not features:
                continue
            
            for reason in data.get('reasons', [])[:min_reasons_per_case]:
                result = self.test_explanation_faithfulness(tx_id, features, reason)
                results.append(result)
                
                # Store result back
                if 'faithfulness_results' not in store[tx_id]:
                    store[tx_id]['faithfulness_results'] = []
                store[tx_id]['faithfulness_results'].append(result)
                store[tx_id]['faithfulness_checked'] = True
                store[tx_id]['faithfulness_passed'] = result.get('passed', False)
        
        # Save updated store
        with open(self.store_path, 'w') as f:
            json.dump(store, f, indent=2)
        
        total = len(results)
        passed = sum(1 for r in results if r.get('passed', False))
        
        return {
            "total_checked": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 3) if total > 0 else 0,
            "results": results
        }
    
    def schedule_faithfulness_check(self, interval_hours: int = 24):
        """Run faithfulness checks on a schedule."""
        from datetime import datetime, timedelta
        import time
        
        logger.info(f"Faithfulness checker started - interval: {interval_hours}h")
        
        while True:
            try:
                logger.info("Running scheduled faithfulness check...")
                result = self.run_faithfulness_checks(sample_size=20)
                logger.info(f"Faithfulness check complete: {result.get('pass_rate', 0)} pass rate")
                
                # Check if pass rate is too low
                if result.get('pass_rate', 1) < 0.6:
                    logger.warning(f"Low faithfulness score: {result.get('pass_rate')}")
                
                time.sleep(interval_hours * 3600)
            except Exception as e:
                logger.error(f"Faithfulness check error: {e}")
                time.sleep(3600)