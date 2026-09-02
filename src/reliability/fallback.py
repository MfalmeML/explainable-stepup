import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FallbackHandler:
    def __init__(self, max_reasons: int = 3):
        self.max_reasons = max_reasons
    
    def get_shap_fallback(self, features: Dict[str, float]) -> List[Dict]:
        """Fallback when SHAP is unavailable."""
        logger.warning("SHAP explainer unavailable - using raw feature fallback")
        # Sort features by absolute value and return top contributors
        sorted_features = sorted(
            features.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        reasons = []
        for feature, value in sorted_features[:self.max_reasons]:
            if abs(value) > 0.01:
                reasons.append({
                    "feature": feature,
                    "value": value,
                    "source": "tabular_fallback",
                    "severity_weight": abs(value)
                })
        return reasons
    
    def get_graph_fallback(self, graph_features: Dict[str, float]) -> List[Dict]:
        """Fallback when graph template config is missing."""
        logger.warning("Graph template config missing - skipping graph reasons")
        return []
    
    def degrade_explanation(self, reasons: List[Dict], degraded_sources: List[str]) -> Dict:
        """Flag an explanation as degraded."""
        return {
            "reasons": reasons,
            "degraded": True,
            "degraded_sources": degraded_sources,
            "message": "Explanation degraded - some sources unavailable"
        }