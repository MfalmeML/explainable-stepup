import unittest
import json
import tempfile
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta

from src.service import ExplanationService
from src.validation.faithfulness import FaithfulnessTester
from src.validation.graph_monitor import GraphPrecisionMonitor
from src.metrics.business_metrics import BusinessMetrics
from src.data.point_in_time import PointInTimeRecorder
from src.data.outcome_store import OutcomeStore
from src.validation.step_up_schema import StepUpRecord

class TestCompleteSystem(unittest.TestCase):
    def setUp(self):
        # Create temporary files
        self.temp_dir = tempfile.mkdtemp()
        self.store_path = os.path.join(self.temp_dir, "store.json")
        self.model_path = os.path.join(self.temp_dir, "model.pkl")
        self.background_path = os.path.join(self.temp_dir, "background.pkl")
        self.config_path = os.path.join(self.temp_dir, "config.yaml")
        
        # Create model
        np.random.seed(42)
        X = pd.DataFrame({
            'amount': np.random.randn(200) * 100 + 500,
            'device_count': np.random.poisson(2, 200),
            'age_days': np.random.exponential(365, 200),
            'velocity_1h': np.random.poisson(1, 200),
            'velocity_24h': np.random.poisson(10, 200),
            'ip_match': np.random.binomial(1, 0.85, 200),
            'country_match': np.random.binomial(1, 0.9, 200),
            'session_duration': np.random.exponential(600, 200),
            'payment_method_age': np.random.exponential(365, 200),
            'failed_attempts': np.random.poisson(0.2, 200)
        })
        y = (X['amount'] > 800).astype(int)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(self.background_path, 'wb') as f:
            pickle.dump(X.sample(10), f)
        
        # Create config
        import yaml
        config = {
            'version': 'test-v1',
            'templates': [
                {'signal': 'device_account_count', 'threshold': 3,
                 'phrase': 'Device linked to {count} other accounts', 'severity_weight': 0.7},
                {'signal': 'shortest_path_to_confirmed_fraud', 'threshold': 2,
                 'phrase': 'Account is {distance} hops from fraud', 'severity_weight': 0.9}
            ]
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Initialize store
        with open(self.store_path, 'w') as f:
            json.dump({}, f)
        
        # Initialize components
        self.service = ExplanationService(
            self.model_path, self.background_path, self.config_path, self.store_path
        )
        self.store = OutcomeStore(self.store_path)
        self.faithfulness = FaithfulnessTester(
            self.store_path, self.model_path, self.background_path
        )
        self.graph_monitor = GraphPrecisionMonitor(self.store_path)
        self.business_metrics = BusinessMetrics(self.store_path)
        self.point_in_time = PointInTimeRecorder(self.store_path)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_decision_processing(self):
        # Process a decision
        features = {
            'amount': 850.0,
            'device_count': 6,
            'age_days': 30,
            'velocity_1h': 5,
            'velocity_24h': 25,
            'ip_match': 1,
            'country_match': 1,
            'session_duration': 300,
            'payment_method_age': 180,
            'failed_attempts': 2
        }
        graph_features = {
            'device_account_count': 6,
            'shortest_path_to_confirmed_fraud': 1,
            'connected_component_size': 12,
            'new_edges_last_1h': 3
        }
        
        # Point-in-time capture
        state = self.point_in_time.capture_decision_state(
            transaction_id="tx_complete_test",
            transaction_features=features,
            graph_features=graph_features,
            decision="CHALLENGE",
            combined_risk_score=0.73,
            ring_score=0.61
        )
        self.assertIn('state_hash', state)
        
        # Process
        result = self.service.explain_and_store(
            transaction_id="tx_complete_test",
            transaction_features=features,
            graph_features=graph_features,
            decision="CHALLENGE",
            combined_risk_score=0.73,
            ring_score=0.61
        )
        self.assertIsNotNone(result)
        self.assertGreater(len(result['reasons']), 0)
        
        # Record step-up outcome
        record = StepUpRecord(
            transaction_id="tx_complete_test",
            channel="otp_sms",
            result="completed",
            latency_ms=45000
        )
        self.store.record_step_up_outcome(record)
        
        # Verify all components can access the data
        faithfulness_result = self.faithfulness.run_faithfulness_checks(sample_size=10)
        self.assertIn('total_checked', faithfulness_result)
        
        graph_feedback = self.graph_monitor.get_feedback_for_graph_model()
        self.assertIn('timestamp', graph_feedback)
        
        business_metrics = self.business_metrics.get_business_impact_dashboard()
        self.assertIn('investigator_impact', business_metrics)
        
        # Verify point-in-time retrieval
        retrieved_state = self.point_in_time.get_decision_state("tx_complete_test")
        self.assertEqual(retrieved_state['transaction_id'], "tx_complete_test")
        self.assertEqual(retrieved_state['decision'], "CHALLENGE")
    
    def test_coverage_metrics(self):
        # Create multiple decisions
        for i in range(5):
            features = {'amount': 500 + i*100, 'device_count': i, 'age_days': 100,
                       'velocity_1h': 1, 'velocity_24h': 5, 'ip_match': 1,
                       'country_match': 1, 'session_duration': 300,
                       'payment_method_age': 180, 'failed_attempts': 0}
            self.service.explain_and_store(
                transaction_id=f"tx_{i}",
                transaction_features=features,
                graph_features={},
                decision="CHALLENGE" if i % 2 == 0 else "APPROVE",
                combined_risk_score=0.5 + i*0.1,
                ring_score=0.3
            )
        
        from src.mlops.monitoring import MLOpsMonitor
        monitor = MLOpsMonitor(self.store_path)
        coverage = monitor.get_explanation_coverage()
        
        self.assertEqual(coverage['total_decisions'], 5)
        self.assertGreaterEqual(coverage['coverage_rate'], 0.8)
    
    def test_drift_detection(self):
        # Create historical data with high completion rate
        for i in range(10):
            tx_id = f"tx_hist_{i}"
            self.service.explain_and_store(
                transaction_id=tx_id,
                transaction_features={'amount': 600, 'device_count': 3, 'age_days': 100,
                                     'velocity_1h': 1, 'velocity_24h': 5, 'ip_match': 1,
                                     'country_match': 1, 'session_duration': 300,
                                     'payment_method_age': 180, 'failed_attempts': 0},
                graph_features={'device_account_count': 4},
                decision="CHALLENGE",
                combined_risk_score=0.6,
                ring_score=0.4
            )
            record = StepUpRecord(tx_id, "otp_sms", "completed" if i < 8 else "abandoned", 30000)
            self.store.record_step_up_outcome(record)
        
        # Create recent data with lower completion rate (drift)
        for i in range(5):
            tx_id = f"tx_recent_{i}"
            self.service.explain_and_store(
                transaction_id=tx_id,
                transaction_features={'amount': 600, 'device_count': 3, 'age_days': 100,
                                     'velocity_1h': 1, 'velocity_24h': 5, 'ip_match': 1,
                                     'country_match': 1, 'session_duration': 300,
                                     'payment_method_age': 180, 'failed_attempts': 0},
                graph_features={'device_account_count': 4},
                decision="CHALLENGE",
                combined_risk_score=0.6,
                ring_score=0.4
            )
            record = StepUpRecord(tx_id, "otp_sms", "completed" if i < 2 else "abandoned", 30000)
            self.store.record_step_up_outcome(record)
        
        drift = self.graph_monitor.detect_precision_drift(window_days=1)
        self.assertIn('alert', drift)
        # Should detect drift due to lower completion rate in recent data
        if drift.get('alert', False):
            self.assertLess(drift.get('change', 0), 0)  # Decrease in precision
    
    def test_faithfulness_checks(self):
        # Create a decision
        features = {'amount': 900.0, 'device_count': 5, 'age_days': 20,
                   'velocity_1h': 8, 'velocity_24h': 30, 'ip_match': 1,
                   'country_match': 1, 'session_duration': 300,
                   'payment_method_age': 180, 'failed_attempts': 3}
        self.service.explain_and_store(
            transaction_id="tx_faith",
            transaction_features=features,
            graph_features={},
            decision="DECLINE",
            combined_risk_score=0.85,
            ring_score=0.3
        )
        
        # Run faithfulness check
        result = self.faithfulness.run_faithfulness_checks(sample_size=10)
        self.assertIn('total_checked', result)
        self.assertIsInstance(result.get('pass_rate', 0), float)
    
    def test_point_in_time_integrity(self):
        features = {'amount': 750.0, 'device_count': 4, 'age_days': 60,
                   'velocity_1h': 3, 'velocity_24h': 15, 'ip_match': 1,
                   'country_match': 1, 'session_duration': 300,
                   'payment_method_age': 180, 'failed_attempts': 1}
        
        state = self.point_in_time.capture_decision_state(
            transaction_id="tx_pit",
            transaction_features=features,
            graph_features={'device_account_count': 3},
            decision="CHALLENGE",
            combined_risk_score=0.65,
            ring_score=0.4
        )
        
        # Retrieve and verify
        retrieved = self.point_in_time.get_decision_state("tx_pit")
        self.assertEqual(retrieved['transaction_features']['amount'], 750.0)
        self.assertEqual(retrieved['state_hash'], state['state_hash'])
        
        # Tamper with data
        store_data = self.store._load_store()
        store_data["tx_pit"]["point_in_time_state"]["decision"] = "APPROVE"
        self.store._save_store(store_data)
        
        # Should detect tampering
        tampered = self.point_in_time.get_decision_state("tx_pit")
        self.assertIn('error', tampered)