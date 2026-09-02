import unittest
import tempfile
import os
import json
from src.data.outcome_store import OutcomeStore
from src.validation.step_up_schema import StepUpRecord


class TestOutcomeStore(unittest.TestCase):
    def setUp(self):
        self.store_path = tempfile.mktemp(suffix='.json')
        self.store = OutcomeStore(self.store_path)

    def tearDown(self):
        if os.path.exists(self.store_path):
            os.remove(self.store_path)

    def test_creates_empty_store_file_if_missing(self):
        self.assertTrue(os.path.exists(self.store_path))
        with open(self.store_path, 'r') as f:
            self.assertEqual(json.load(f), {})

    def test_save_and_get_decision_record(self):
        self.store.save_decision_record(
            transaction_id='tx_1',
            decision='CHALLENGE',
            combined_risk_score=0.6,
            ring_score=0.3,
            reasons=[{"text": "New device", "source": "tabular", "weight": 0.5}],
            override_driven=False,
            reason_template_version='test-v1'
        )
        record = self.store.get_decision('tx_1')
        self.assertIsNotNone(record)
        self.assertEqual(record['decision'], 'CHALLENGE')
        self.assertEqual(record['combined_risk_score'], 0.6)
        self.assertEqual(record['ring_score'], 0.3)
        self.assertIn('decision_timestamp', record)

    def test_get_decision_returns_none_for_missing_transaction(self):
        self.assertIsNone(self.store.get_decision('does_not_exist'))

    def test_record_step_up_outcome_updates_existing_record(self):
        self.store.save_decision_record(
            transaction_id='tx_1',
            decision='CHALLENGE',
            combined_risk_score=0.6,
            ring_score=0.3,
            reasons=[],
            override_driven=False,
            reason_template_version='test-v1'
        )
        step_up = StepUpRecord(
            transaction_id='tx_1',
            channel='otp_sms',
            result='completed',
            latency_ms=15000,
            timestamp='2026-01-01T00:00:00+00:00'
        )
        ok = self.store.record_step_up_outcome(step_up)
        self.assertTrue(ok)

        record = self.store.get_decision('tx_1')
        self.assertEqual(record['step_up_result'], 'completed')
        self.assertEqual(record['step_up_channel'], 'otp_sms')
        self.assertEqual(record['step_up_latency_ms'], 15000)
        self.assertEqual(record['step_up_timestamp'], '2026-01-01T00:00:00+00:00')

    def test_record_step_up_outcome_returns_false_for_unknown_transaction(self):
        step_up = StepUpRecord(
            transaction_id='does_not_exist',
            channel='otp_sms',
            result='completed',
            latency_ms=15000,
            timestamp='2026-01-01T00:00:00+00:00'
        )
        ok = self.store.record_step_up_outcome(step_up)
        self.assertFalse(ok)

    def test_completion_rate_by_category_groups_and_computes_rate(self):
        for i in range(6):
            tx_id = f'tx_{i}'
            self.store.save_decision_record(
                transaction_id=tx_id,
                decision='CHALLENGE',
                combined_risk_score=0.6,
                ring_score=0.3,
                reasons=[{"text": "New device", "source": "tabular", "weight": 0.5}],
                override_driven=False,
                reason_template_version='test-v1'
            )
            result = 'completed' if i < 4 else 'abandoned'  # 4/6 completed
            self.store.record_step_up_outcome(StepUpRecord(
                transaction_id=tx_id,
                channel='otp_sms',
                result=result,
                latency_ms=15000,
                timestamp='2026-01-01T00:00:00+00:00'
            ))

        rates = self.store.get_step_up_completion_rate_by_category(min_cases=5)
        self.assertIn('new_device', rates)
        self.assertEqual(rates['new_device']['total'], 6)
        self.assertEqual(rates['new_device']['completion_rate'], round(4 / 6, 3))

    def test_completion_rate_by_category_filters_below_min_cases(self):
        self.store.save_decision_record(
            transaction_id='tx_1',
            decision='CHALLENGE',
            combined_risk_score=0.6,
            ring_score=0.3,
            reasons=[{"text": "New device", "source": "tabular", "weight": 0.5}],
            override_driven=False,
            reason_template_version='test-v1'
        )
        self.store.record_step_up_outcome(StepUpRecord(
            transaction_id='tx_1', channel='otp_sms', result='completed',
            latency_ms=15000, timestamp='2026-01-01T00:00:00+00:00'
        ))
        rates = self.store.get_step_up_completion_rate_by_category(min_cases=5)
        self.assertNotIn('new_device', rates)

    def test_completion_rate_excludes_approve_decisions(self):
        self.store.save_decision_record(
            transaction_id='tx_approve',
            decision='APPROVE',
            combined_risk_score=0.1,
            ring_score=0.0,
            reasons=[],
            override_driven=False,
            reason_template_version='test-v1'
        )
        # APPROVE records have no step_up_result, so they should never surface
        rates = self.store.get_step_up_completion_rate_by_category(min_cases=1)
        self.assertEqual(rates, {})

    def test_determine_category_maps_known_reason_text(self):
        cases = [
            ("New device linked to account", "new_device"),
            ("Linked to confirmed fraud ring", "fraud_ring"),
            ("Part of connected fraud network", "network"),
            ("Amount far from normal spending", "amount_anomaly"),
            ("High velocity of transactions", "velocity"),
            ("IP address mismatch", "ip_mismatch"),
            ("Something totally unrelated", "other"),
        ]
        for text, expected_category in cases:
            reasons = [{"text": text, "source": "tabular", "weight": 0.5}]
            self.assertEqual(self.store._determine_category(reasons), expected_category)

    def test_determine_category_returns_unknown_for_empty_reasons(self):
        self.assertEqual(self.store._determine_category([]), "unknown")

    def test_determine_category_filters_by_source(self):
        reasons = [
            {"text": "New device", "source": "graph", "weight": 0.9},
            {"text": "Amount far from normal spending", "source": "tabular", "weight": 0.5},
        ]
        # Only tabular reasons should be considered
        self.assertEqual(self.store._determine_category(reasons, source="tabular"), "amount_anomaly")
        self.assertEqual(self.store._determine_category(reasons, source="graph"), "new_device")


if __name__ == '__main__':
    unittest.main()