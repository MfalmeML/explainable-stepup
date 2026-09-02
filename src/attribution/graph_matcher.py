import yaml
from typing import Dict, List, Any

# Signals where a LOWER value indicates higher risk (e.g. distance-based
# signals: fewer hops to a known fraud node = more suspicious). Every other
# signal defaults to "higher value = more suspicious" (value >= threshold).
# This is a legacy fallback for template configs that don't specify an
# explicit "direction" field (see match_signals below) -- prefer adding
# `direction: lower_is_worse` to the YAML template instead of relying on
# signal name matching here, since name-based matching silently breaks
# whenever a signal is renamed (e.g. "shortest_path" vs
# "shortest_path_to_confirmed_fraud").
LOWER_IS_WORSE = {"shortest_path"}


class _AnyPlaceholder(dict):
    """Lets phrase.format_map() accept any placeholder name (e.g. {count},
    {distance}, {size}, ...) by resolving every one to the same matched
    value, instead of requiring the caller to know every placeholder name
    templates might use in advance."""
    def __init__(self, value):
        self._value = value

    def __missing__(self, key):
        return self._value


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

            direction = template.get("direction")
            if direction == "lower_is_worse":
                triggered = value <= threshold
            elif direction == "higher_is_worse":
                triggered = value >= threshold
            elif signal in LOWER_IS_WORSE:
                triggered = value <= threshold
            else:
                triggered = value >= threshold

            if not triggered:
                continue

            severity_weight = template["severity_weight"]
            phrase = template["phrase"].format_map(_AnyPlaceholder(value))

            matches.append({
                "signal": signal,
                "value": value,
                "phrase": phrase,
                "weight": severity_weight,
                "severity_weight": severity_weight,
                "source": "graph",
            })

        matches.sort(key=lambda m: m["severity_weight"], reverse=True)
        return matches