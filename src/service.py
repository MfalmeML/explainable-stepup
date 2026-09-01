from src.attribution.shap_wrapper import ShapAttributor
from src.attribution.graph_matcher import GraphTemplateMatcher
from src.ranking.ranker import ReasonRanker
from src.data.outcome_store import OutcomeStore
from typing import Dict, List, Any, Optional

class ExplanationService:
    def __init__(
        self, 
        model_path: str, 
        background_path: str, 
        template_config_path: str,
        store_path: str
    ):
        self.shap = ShapAttributor(model_path, background_path)
        self.graph = GraphTemplateMatcher(template_config_path)
        self.ranker = ReasonRanker(max_reasons=3)
        self.store = OutcomeStore(store_path)
        self.template_version = self.graph.version
    
    def explain_and_store(
        self, 
        transaction_id: str,
        transaction_features: Dict[str, float],
        graph_features: Dict[str, float],
        decision: str,
        combined_risk_score: float,
        ring_score: float,
        override_triggered: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Generate explanation and store decision record."""
        
        if decision == "APPROVE":
            # Still store the APPROVE record without reasons
            self.store.save_decision_record(
                transaction_id=transaction_id,
                decision=decision,
                combined_risk_score=combined_risk_score,
                ring_score=ring_score,
                reasons=[],
                override_driven=False,
                reason_template_version=self.template_version
            )
            return None
        
        # Generate explanation
        if override_triggered:
            result = {
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
        else:
            shap_reasons = self.shap.get_attributions(transaction_features)
            graph_reasons = self.graph.match_signals(graph_features)
            selected = self.ranker.select_top_reasons(shap_reasons, graph_reasons)
            
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
            
            result = {
                "reasons": formatted_reasons,
                "override_driven": False,
                "reason_template_version": self.template_version
            }
        
        # Store the decision record
        self.store.save_decision_record(
            transaction_id=transaction_id,
            decision=decision,
            combined_risk_score=combined_risk_score,
            ring_score=ring_score,
            reasons=result["reasons"],
            override_driven=result["override_driven"],
            reason_template_version=result["reason_template_version"]
        )
        
        return result