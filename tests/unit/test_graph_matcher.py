import unittest
import tempfile
import yaml
import os
from src.attribution.graph_matcher import GraphTemplateMatcher

class TestGraphMatcher(unittest.TestCase):
    def setUp(self):
        self.config_content = """
version: "test-v1"
templates:
  - signal: device_account_count
    threshold: 5
    phrase: "Device linked to {count} other accounts"
    severity_weight: 0.7
  - signal: shortest_path
    threshold: 2
    phrase: "Account is {distance} hops from fraud"
    severity_weight: 0.9
"""
        self.config_path = tempfile.mktemp(suffix='.yaml')
        with open(self.config_path, 'w') as f:
            f.write(self.config_content)
    
    def tearDown(self):
        os.remove(self.config_path)
    
    def test_matches_above_threshold(self):
        matcher = GraphTemplateMatcher(self.config_path)
        features = {'device_account_count': 6, 'shortest_path': 1}
        result = matcher.match_signals(features)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['signal'], 'shortest_path')
        self.assertEqual(result[1]['signal'], 'device_account_count')
    
    def test_skips_below_threshold(self):
        matcher = GraphTemplateMatcher(self.config_path)
        features = {'device_account_count': 4, 'shortest_path': 3}
        result = matcher.match_signals(features)
        self.assertEqual(len(result), 0)
    
    def test_handles_missing_features(self):
        matcher = GraphTemplateMatcher(self.config_path)
        features = {'other_signal': 10}
        result = matcher.match_signals(features)
        self.assertEqual(len(result), 0)
    
    def test_phrase_interpolation(self):
        matcher = GraphTemplateMatcher(self.config_path)
        features = {'device_account_count': 6, 'shortest_path': 1}
        result = matcher.match_signals(features)
        self.assertIn('6', result[1]['phrase'])  # device_account_count matched second