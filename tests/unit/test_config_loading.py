import unittest
import yaml
import json

class TestConfigLoading(unittest.TestCase):
    def test_template_yaml_loads(self):
        with open('config/templates/graph_reason_templates.yaml', 'r') as f:
            config = yaml.safe_load(f)
        self.assertIn('templates', config)
        self.assertGreater(len(config['templates']), 0)
    
    def test_version_manifest_loads(self):
        with open('config/templates/version_manifest.json', 'r') as f:
            manifest = json.load(f)
        self.assertIn('current_version', manifest)