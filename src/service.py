from src.attribution.shap_wrapper import ShapAttributor
from src.attribution.graph_matcher import GraphTemplateMatcher
from src.ranking.ranker import ReasonRanker
from typing import Dict, List, Any, Optional

class ExplanationService:
    def __init__(self, model_path: str, background_path: str, template_config_path: str):
        self.shap = ShapAttributor(model_path, background_path)
        self.graph = GraphTemplateMatcher(template_config_path)
        self.ranker = ReasonRanker(max_reasons=3)
        self.template_version = self.graph.version
    
    def explain_decision(
        self, 
        transaction_features: Dict[str, float],
        graph_features: Dict[str, float],
        decision: str,
        override_triggered: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Generate explanation for non-APPROVE decisions."""
        
        if decision == "APPROVE":
            return None
        
        # Handle override case
        if override_triggered:
            return {
                "reasons": [
                    {
                        "text": "Declined due to confirmed fraud ring membership",
                        "source": "override",
                        "weight": 1.0
                    }
                ],
                "override_driven": True,
                "reason_template_version": self.template_version
            }
        
        # Normal case: combine tabular and graph
        shap_reasons = self.shap.get_attributions(transaction_features)
        graph_reasons = self.graph.match_signals(graph_features)
        
        selected = self.ranker.select_top_reasons(shap_reasons, graph_reasons)
        
        # Format output with text field
        formatted_reasons = []
        for reason in selected:
            if reason.get('source') == 'graph':
                text = reason.get('phrase', '')
            else:
                text = f"{reason.get('feature', 'unknown')} = {reason.get('value', 0):.2f}"
            
            formatted_reasons.append({
                "text": text,
                "source": reason.get('source', 'unknown'),
                "weight": reason.get('severity_weight', 0)
            })
        
        return {
            "reasons": formatted_reasons,
            "override_driven": False,
            "reason_template_version": self.template_version
        }