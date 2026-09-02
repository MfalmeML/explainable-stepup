import unittest
import tempfile
import os
import json
from src.data.outcome_store import OutcomeStore
from src.validation.metrics import ValidationMetrics
from src.validation.step_up_schema import StepUpRecord
from datetime import datetime, timedelta

class TestValidationLoop(unittest.TestCase):
    def setUp(self):
        self.store_path = tempfile.mktemp(suffix='.json')
        self.store = OutcomeStore(self.store_path)
        self.metrics = ValidationMetrics(self.store_path)
        
        # Create test data with multiple categories and score buckets
        categories = [
            ("new_device", 0.2),
            ("fraud_ring", 0.8),
            ("network", 0.5),
            ("amount_anomaly", 0.3)
        ]
        
        now = datetime.utcnow()
        
        for i, (category, ring_score) in enumerate(categories):
            for j in range(10):
                tx_id = f"tx_{category}_{j}"
                is_completed = j < 7  # 70% completion rate
                
                reasons = [{"text": category.replace("_", " "), "source": "tabular", "weight": 0.7}]
                if category == "new_device":
                    reasons[0]["text"] = "New device"
                elif category == "fraud_ring":
                    reasons[0]["text"] = "Linked to confirmed fraud ring"
                elif category == "network":
                    reasons[0]["text"] = "Part of connected fraud network"
                
                self.store.save_decision_record(
                    transaction_id=tx_id,
                    decision="CHALLENGE",
                    combined_risk_score=0.6 + (i * 0.1),
                    ring_score=ring_score,
                    reasons=reasons,
                    override_driven=False,
                    reason_template_version="test-v1"
                )
                
                result = "completed" if is_completed else "abandoned"
                timestamp = (now - timedelta(hours=j)).isoformat()
                record = StepUpRecord(
                    transaction_id=tx_id,
                    channel="otp_sms",
                    result=result,
                    latency_ms=30000 + j * 1000,
                    timestamp=timestamp
                )
                self.store.record_step_up_outcome(record)
    
    def tearDown(self):
        if os.path.exists(self.store_path):
            os.remove(self.store_path)
    
    def test_completion_rate_by_category(self):
        rates = self.metrics.get_completion_rate_by_category(min_cases=3)
        self.assertIn("new_device", rates)
        self.assertEqual(rates["new_device"]["completion_rate"], 0.7)
        self.assertIn("fraud_ring", rates)
        self.assertEqual(rates["fraud_ring"]["completion_rate"], 0.7)
    
    def test_completion_rate_by_score_bucket(self):
        rates = self.metrics.get_completion_rate_by_score_bucket(min_cases=3)
        self.assertGreater(len(rates), 0)
    
    def test_trend_by_category(self):
        trend = self.metrics.get_trend_by_category(days=7, min_cases=1)
        self.assertIn("new_device", trend)
        self.assertGreater(len(trend["new_device"]), 0)
    
    def test_detect_drift(self):
        # Add data for a category with different rate
        for i in range(5):
            tx_id = f"tx_drift_{i}"
            reasons = [{"text": "new device", "source": "tabular", "weight": 0.7}]
            self.store.save_decision_record(
                transaction_id=tx_id,
                decision="CHALLENGE",
                combined_risk_score=0.7,
                ring_score=0.3,
                reasons=reasons,
                override_driven=False,
                reason_template_version="test-v1"
            )
            result = "abandoned" if i < 3 else "completed"  # 40% completion rate
            timestamp = datetime.utcnow().isoformat()
            record = StepUpRecord(
                transaction_id=tx_id,
                channel="otp_sms",
                result=result,
                latency_ms=30000,
                timestamp=timestamp
            )
            self.store.record_step_up_outcome(record)
        
        alerts = self.metrics.detect_drift(threshold_change=0.1, min_cases=3)
        self.assertIn("new_device", alerts)