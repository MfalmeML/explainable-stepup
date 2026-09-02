import unittest
import pickle
import tempfile
import os
import yaml
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from src.service import ExplanationService

class TestExplanationService(unittest.TestCase):
    def setUp(self):
        # Create mock model
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
        
        self.model_path = tempfile.mktemp(suffix='.pkl')
        self.background_path = tempfile.mktemp(suffix='.pkl')
        self.config_path = tempfile.mktemp(suffix='.yaml')
        self.store_path = tempfile.mktemp(suffix='.json')
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.background_path, 'wb') as f:
            pickle.dump(self.background, f)
        
        config = {
            'version': 'test-v1',
            'templates': [
                {'signal': 'device_account_count', 'threshold': 5, 
                 'phrase': 'Device linked to {count} other accounts', 'severity_weight': 0.7},
                {'signal': 'shortest_path', 'threshold': 2,
                 'phrase': 'Account is {distance} hops from fraud', 'severity_weight': 0.9}
            ]
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f)
        
        self.service = ExplanationService(
            self.model_path, self.background_path, self.config_path, self.store_path
        )
    
    def tearDown(self):
        os.remove(self.model_path)
        os.remove(self.background_path)
        os.remove(self.config_path)
        if os.path.exists(self.store_path):
            os.remove(self.store_path)
    
    def test_approve_returns_none(self):
        result = self.service.explain_and_store(
            transaction_id='tx_approve',
            transaction_features={'amount': 0.0, 'device_count': 0.0, 'age_days': 0.0},
            graph_features={},
            decision='APPROVE',
            combined_risk_score=0.1,
            ring_score=0.0
        )
        self.assertIsNone(result)
    
    def test_challenge_returns_reasons(self):
        transaction = {'amount': 5.0, 'device_count': 6.0, 'age_days': 0.5}
        graph = {'device_account_count': 6, 'shortest_path': 1}
        
        result = self.service.explain_and_store(
            transaction_id='tx_challenge',
            transaction_features=transaction,
            graph_features=graph,
            decision='CHALLENGE',
            combined_risk_score=0.6,
            ring_score=0.2
        )
        
        self.assertIsNotNone(result)
        self.assertFalse(result['override_driven'])
        self.assertEqual(result['reason_template_version'], 'test-v1')
        self.assertGreater(len(result['reasons']), 0)
    
    def test_override_driven_returns_override_reason(self):
        result = self.service.explain_and_store(
            transaction_id='tx_override',
            transaction_features={'amount': 5.0},
            graph_features={},
            decision='DECLINE',
            combined_risk_score=0.95,
            ring_score=0.9,
            override_triggered=True
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result['override_driven'])
        self.assertEqual(result['reasons'][0]['source'], 'override')
        self.assertEqual(result['reasons'][0]['text'], 'Declined due to confirmed fraud ring membership')
    
    def test_decline_returns_reasons(self):
        transaction = {'amount': -5.0, 'device_count': -5.0, 'age_days': 0.5}
        graph = {'device_account_count': 0, 'shortest_path': 5}
        
        result = self.service.explain_and_store(
            transaction_id='tx_decline',
            transaction_features=transaction,
            graph_features=graph,
            decision='DECLINE',
            combined_risk_score=0.85,
            ring_score=0.3
        )
        
        self.assertIsNotNone(result)
        self.assertFalse(result['override_driven'])

    def test_explain_and_store_persists_decision_record(self):
        transaction = {'amount': 5.0, 'device_count': 6.0, 'age_days': 0.5}
        graph = {'device_account_count': 6, 'shortest_path': 1}

        self.service.explain_and_store(
            transaction_id='tx_persist',
            transaction_features=transaction,
            graph_features=graph,
            decision='CHALLENGE',
            combined_risk_score=0.6,
            ring_score=0.2
        )

        stored = self.service.store.get_decision('tx_persist')
        self.assertIsNotNone(stored)
        self.assertEqual(stored['decision'], 'CHALLENGE')
        self.assertEqual(stored['combined_risk_score'], 0.6)
        self.assertEqual(stored['ring_score'], 0.2)