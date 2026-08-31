import yaml
from typing import Dict, List, Any

class GraphTemplateMatcher:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def match_signals(self, graph_features: Dict[str, float]) -> List[Dict[str, Any]]:
        # Returns: [{"signal": "device_account_count", "value": 6, "phrase": "...", "weight": 0.7}, ...]
        raise NotImplementedError("Implement in Sprint 2")