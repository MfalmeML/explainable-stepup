import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional

from src.service import ExplanationService
from src.reliability.fallback import FallbackHandler
from src.mlops.monitoring import MLOpsMonitor
from src.validation.metrics import ValidationMetrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionSystem:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.service = ExplanationService(
            model_path=self.config["model_path"],
            background_path=self.config["background_path"],
            template_config_path=self.config["template_config_path"],
            store_path=self.config["store_path"]
        )
        self.fallback = FallbackHandler(max_reasons=self.config.get("max_reasons", 3))
        self.monitor = MLOpsMonitor(self.config["store_path"])
        self.metrics = ValidationMetrics(self.config["store_path"])
    
    def process_with_fallback(
        self,
        transaction_id: str,
        transaction_features: Dict[str, float],
        graph_features: Dict[str, float],
        decision: str,
        combined_risk_score: float,
        ring_score: float,
        override_triggered: bool = False
    ) -> Dict:
        """Process with fallback handling for reliability."""
        degraded_sources = []
        
        try:
            # Attempt normal processing
            result = self.service.explain_and_store(
                transaction_id=transaction_id,
                transaction_features=transaction_features,
                graph_features=graph_features,
                decision=decision,
                combined_risk_score=combined_risk_score,
                ring_score=ring_score,
                override_triggered=override_triggered
            )
            return result
        except Exception as e:
            logger.error(f"Normal processing failed for {transaction_id}: {e}")
            
            # Fallback: generate degraded explanation
            reasons = []
            
            # Try SHAP fallback
            try:
                shap_reasons = self.fallback.get_shap_fallback(transaction_features)
                reasons.extend(shap_reasons)
            except Exception as e2:
                logger.error(f"SHAP fallback failed: {e2}")
                degraded_sources.append("shap")
            
            # Try graph fallback
            try:
                graph_reasons = self.fallback.get_graph_fallback(graph_features)
                reasons.extend(graph_reasons)
            except Exception as e2:
                logger.error(f"Graph fallback failed: {e2}")
                degraded_sources.append("graph")
            
            # Rank and select
            from src.ranking.ranker import ReasonRanker
            ranker = ReasonRanker(max_reasons=self.config.get("max_reasons", 3))
            selected = ranker.select_top_reasons(
                [r for r in reasons if r.get("source") != "graph_fallback"],
                [r for r in reasons if r.get("source") == "graph_fallback"]
            )
            
            # Format
            formatted = []
            for reason in selected:
                text = reason.get("text", f"{reason.get('feature', 'unknown')} = {reason.get('value', 0):.2f}")
                formatted.append({
                    "text": text,
                    "source": reason.get("source", "unknown"),
                    "weight": reason.get("severity_weight", 0)
                })
            
            result = {
                "reasons": formatted,
                "override_driven": override_triggered,
                "reason_template_version": self.service.template_version,
                "degraded": True,
                "degraded_sources": degraded_sources
            }
            
            # Store degraded explanation
            try:
                self.service.store.save_decision_record(
                    transaction_id=transaction_id,
                    decision=decision,
                    combined_risk_score=combined_risk_score,
                    ring_score=ring_score,
                    reasons=result["reasons"],
                    override_driven=result["override_driven"],
                    reason_template_version=result["reason_template_version"]
                )
            except Exception as e3:
                logger.error(f"Failed to store degraded explanation: {e3}")
            
            return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <config_path> [command]")
        print("Commands: process, dashboard, coverage, drift")
        sys.exit(1)
    
    config_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "process"
    
    system = ProductionSystem(config_path)
    
    if command == "process":
        # Example processing
        result = system.process_with_fallback(
            transaction_id=f"tx_{datetime.utcnow().timestamp():.0f}",
            transaction_features={
                "amount": 850.00,
                "device_count": 6,
                "age_days": 30,
                "velocity_1h": 5
            },
            graph_features={
                "device_account_count": 6,
                "shortest_path_to_confirmed_fraud": 1,
                "connected_component_size": 12
            },
            decision="CHALLENGE",
            combined_risk_score=0.73,
            ring_score=0.61
        )
        print(json.dumps(result, indent=2))
    
    elif command == "dashboard":
        dashboard = system.monitor.get_mlops_dashboard()
        print(json.dumps(dashboard, indent=2))
    
    elif command == "coverage":
        coverage = system.monitor.get_explanation_coverage()
        print(json.dumps(coverage, indent=2))
    
    elif command == "drift":
        alerts = system.metrics.detect_drift()
        print(json.dumps(alerts, indent=2))
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()