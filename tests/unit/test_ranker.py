import unittest
from src.ranking.ranker import ReasonRanker

class TestReasonRanker(unittest.TestCase):
    def setUp(self):
        self.ranker = ReasonRanker(max_reasons=3)
        
        self.tabular_reasons = [
            {"feature": "amount", "shap_value": 0.5, "severity_weight": 0.5, "source": "tabular"},
            {"feature": "device_count", "shap_value": 0.3, "severity_weight": 0.3, "source": "tabular"},
            {"feature": "age_days", "shap_value": 0.2, "severity_weight": 0.2, "source": "tabular"},
            {"feature": "velocity", "shap_value": 0.1, "severity_weight": 0.1, "source": "tabular"}
        ]
        
        self.graph_reasons = [
            {"signal": "device_account_count", "severity_weight": 0.8, "source": "graph"},
            {"signal": "shortest_path", "severity_weight": 0.9, "source": "graph"}
        ]
    
    def test_combines_both_sources(self):
        result = self.ranker.select_top_reasons(self.tabular_reasons, self.graph_reasons)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['signal'], 'shortest_path')
        self.assertEqual(result[1]['signal'], 'device_account_count')
        self.assertEqual(result[2]['feature'], 'amount')
    
    def test_deduplicates_by_feature_name(self):
        # Create overlapping reasons
        tabular = [{"feature": "device_count", "shap_value": 0.3, "severity_weight": 0.3, "source": "tabular"}]
        graph = [{"signal": "device_count", "severity_weight": 0.7, "source": "graph"}]
        
        result = self.ranker.select_top_reasons(tabular, graph)
        self.assertEqual(len(result), 1)
        # Graph should win due to higher weight
        self.assertEqual(result[0]['source'], 'graph')
    
    def test_returns_empty_when_no_reasons(self):
        result = self.ranker.select_top_reasons([], [])
        self.assertEqual(result, [])
    
    def test_caps_at_max_reasons(self):
        self.ranker.max_reasons = 2
        result = self.ranker.select_top_reasons(self.tabular_reasons, self.graph_reasons)
        self.assertEqual(len(result), 2)
    
    def test_handles_missing_severity_weight(self):
        reasons = [{"feature": "amount", "source": "tabular"}]  # No severity_weight
        result = self.ranker.select_top_reasons(reasons, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['feature'], 'amount')