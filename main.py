import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional

from src.service import ExplanationService
from src.api.handlers import APIHandlers
from src.api.step_up_handler import StepUpHandler
from src.api.validation_handler import ValidationHandler
from src.ui.investigator_view import InvestigatorView

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExplainableDecisioningSystem:
    def __init__(
        self,
        model_path: str,
        background_path: str,
        template_config_path: str,
        store_path: str
    ):
        self.service = ExplanationService(
            model_path=model_path,
            background_path=background_path,
            template_config_path=template_config_path,
            store_path=store_path
        )
        self.api_handlers = APIHandlers(store_path)
        self.step_up_handler = StepUpHandler(store_path)
        self.validation_handler = ValidationHandler(store_path)
        self.investigator_view = InvestigatorView(store_path)
    
    def process_decision(
        self,
        transaction_id: str,
        transaction_features: Dict[str, float],
        graph_features: Dict[str, float],
        decision: str,
        combined_risk_score: float,
        ring_score: float,
        override_triggered: bool = False
    ) -> Dict:
        """Process a decision and generate explanation."""
        try:
            result = self.service.explain_and_store(
                transaction_id=transaction_id,
                transaction_features=transaction_features,
                graph_features=graph_features,
                decision=decision,
                combined_risk_score=combined_risk_score,
                ring_score=ring_score,
                override_triggered=override_triggered
            )
            
            # If decision is CHALLENGE, trigger step-up (simulated)
            if decision == "CHALLENGE":
                self._trigger_step_up(transaction_id)
            
            return {
                "status": "processed",
                "transaction_id": transaction_id,
                "decision": decision,
                "explanation": result
            }
        except Exception as e:
            logger.error(f"Error processing decision {transaction_id}: {e}")
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "error": str(e)
            }
    
    def _trigger_step_up(self, transaction_id: str):
        """Simulate step-up trigger. In production, this would call the OTP service."""
        logger.info(f"Step-up triggered for transaction {transaction_id}")
        # Store would be updated when step-up completes via the API
    
    def get_case(self, transaction_id: str) -> Dict:
        return self.investigator_view.get_case_detail(transaction_id)
    
    def record_agreement(
        self,
        transaction_id: str,
        investigator_id: str,
        agreement: bool,
        notes: Optional[str] = None
    ) -> Dict:
        return self.investigator_view.record_reason_agreement(
            transaction_id, investigator_id, agreement, notes
        )
    
    def record_step_up_outcome(
        self,
        transaction_id: str,
        channel: str,
        result: str,
        latency_ms: int
    ) -> Dict:
        return self.step_up_handler.handle_step_up_capture({
            "transaction_id": transaction_id,
            "channel": channel,
            "result": result,
            "latency_ms": latency_ms
        })
    
    def get_validation_dashboard(self) -> Dict:
        return self.validation_handler.handle_dashboard_stats()
    
    def get_completion_rates(self) -> Dict:
        return self.validation_handler.handle_validation_stats()
    
    def check_drift(self) -> Dict:
        return self.validation_handler.handle_drift_check()

def main():
    """Example usage of the complete system."""
    # Configuration
    config = {
        "model_path": "models/tabular_model.pkl",
        "background_path": "models/background_data.pkl",
        "template_config_path": "config/templates/graph_reason_templates.yaml",
        "store_path": "outcome_store.json"
    }
    
    # Initialize system
    system = ExplainableDecisioningSystem(**config)
    
    # Example transaction
    transaction_features = {
        "amount": 850.00,
        "device_count": 6,
        "age_days": 30,
        "velocity_1h": 5
    }
    
    graph_features = {
        "device_account_count": 6,
        "shortest_path_to_confirmed_fraud": 1,
        "connected_component_size": 12,
        "new_edges_last_1h": 3
    }
    
    # Process decision
    result = system.process_decision(
        transaction_id="tx_99999",
        transaction_features=transaction_features,
        graph_features=graph_features,
        decision="CHALLENGE",
        combined_risk_score=0.73,
        ring_score=0.61,
        override_triggered=False
    )
    
    print("Decision processed:", json.dumps(result, indent=2))
    
    # Get case detail
    case = system.get_case("tx_99999")
    print("\nCase detail:", json.dumps(case, indent=2))

if __name__ == "__main__":
    main()