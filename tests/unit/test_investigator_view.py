import unittest
import json
import tempfile
import os
from src.ui.investigator_view import InvestigatorView

class TestInvestigatorView(unittest.TestCase):
    def setUp(self):
        self.store_path = tempfile.mktemp(suffix='.json')
        
        # Create test data
        store = {
            "tx_1": {
                "transaction_id": "tx_1",
                "decision": "CHALLENGE",
                "combined_risk_score": 0.8,
                "reasons": [{"text": "Test reason", "source": "tabular", "weight": 0.5}],
                "override_driven": False
            },
            "tx_2": {
                "transaction_id": "tx_2",
                "decision": "APPROVE",
                "combined_risk_score": 0.1
            }
        }
        with open(self.store_path, 'w') as f:
            json.dump(store, f)
        
        self.view = InvestigatorView(self.store_path)
    
    def tearDown(self):
        if os.path.exists(self.store_path):
            os.remove(self.store_path)
    
    def test_get_case_detail_returns_case(self):
        case = self.view.get_case_detail("tx_1")
        self.assertEqual(case["transaction_id"], "tx_1")
        self.assertEqual(case["decision"], "CHALLENGE")
        self.assertEqual(len(case["reasons"]), 1)
    
    def test_get_case_detail_returns_error_if_not_found(self):
        case = self.view.get_case_detail("tx_999")
        self.assertIn("error", case)
    
    def test_record_reason_agreement_stores_agreement(self):
        result = self.view.record_reason_agreement("tx_1", "inv_1", True)
        self.assertEqual(result["status"], "recorded")
        
        # Verify stored
        with open(self.store_path, 'r') as f:
            store = json.load(f)
        self.assertEqual(store["tx_1"]["reason_agreement"], 1)
        self.assertEqual(store["tx_1"]["investigator_id"], "inv_1")
    
    def test_get_review_sample_returns_unreviewed(self):
        sample = self.view.get_review_sample(10)
        self.assertGreater(len(sample), 0)
        # tx_2 is APPROVE so should not be in sample
        tx_ids = [s["transaction_id"] for s in sample]
        self.assertNotIn("tx_2", tx_ids)