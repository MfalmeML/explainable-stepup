import yaml
from typing import Dict, List, Any

# Signals where a LOWER value indicates higher risk (e.g. distance-based
# signals: fewer hops to a known fraud node = more suspicious). Every other
# signal is treated as "higher value = more suspicious" (value >= threshold).
# NOTE: this direction isn't expressed in the YAML config, so any new
# distance-like signal added in Sprint 2+ must be added here too, or it will
# silently use the wrong comparison.
LOWER_IS_WORSE = {"shortest_path"}


class GraphTemplateMatcher:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.templates = self.config.get("templates", [])
        self.version = self.config.get("version")

    def match_signals(self, graph_features: Dict[str, float]) -> List[Dict[str, Any]]:
        # Returns: [{"signal": "device_account_count", "value": 6, "phrase": "...", "weight": 0.7}, ...]
        matches = []
        for template in self.templates:
            signal = template["signal"]
            if signal not in graph_features:
                continue

            value = graph_features[signal]
            threshold = template["threshold"]

            if signal in LOWER_IS_WORSE:
                triggered = value <= threshold
            else:
                triggered = value >= threshold

            if not triggered:
                continue

            severity_weight = template["severity_weight"]
            phrase = template["phrase"].format(count=value, distance=value)

            matches.append({
                "signal": signal,
                "value": value,
                "phrase": phrase,
                "weight": severity_weight,
                "severity_weight": severity_weight,
            })

        matches.sort(key=lambda m: m["severity_weight"], reverse=True)
        return matches