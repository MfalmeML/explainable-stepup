import json
import logging
import time
import os
from typing import Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecisionConsumer:
    def __init__(
        self,
        store_path: str,
        model_path: str,
        background_path: str,
        template_config_path: str,
        poll_interval: int = 1
    ):
        self.store_path = store_path
        self.poll_interval = poll_interval
        self.running = False
        
        # Import here to avoid circular imports
        from src.service import ExplanationService
        self.service = ExplanationService(
            model_path=model_path,
            background_path=background_path,
            template_config_path=template_config_path,
            store_path=store_path
        )
    
    def start(self):
        """Start consuming decisions from a queue."""
        self.running = True
        logger.info("Decision consumer started")
        
        while self.running:
            try:
                # In production, this would poll a message queue
                # Simulated queue polling
                decision = self._poll_queue()
                if decision:
                    self._process_decision(decision)
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                time.sleep(self.poll_interval * 5)
    
    def stop(self):
        self.running = False
        logger.info("Decision consumer stopped")
    
    def _poll_queue(self) -> Optional[Dict]:
        """Poll for decisions. Replace with actual queue implementation."""
        # For demo, read from a queue file
        queue_path = "/tmp/decision_queue.jsonl"
        if not os.path.exists(queue_path):
            return None
        
        try:
            with open(queue_path, 'r') as f:
                lines = f.readlines()
            if not lines:
                return None
            
            # Process first line
            decision = json.loads(lines[0].strip())
            
            # Remove processed line
            with open(queue_path, 'w') as f:
                f.writelines(lines[1:])
            
            return decision
        except Exception as e:
            logger.error(f"Queue poll error: {e}")
            return None
    
    def _process_decision(self, decision: Dict):
        """Process a single decision."""
        try:
            transaction_id = decision.get("transaction_id")
            if not transaction_id:
                logger.warning("Decision missing transaction_id")
                return
            
            result = self.service.explain_and_store(
                transaction_id=transaction_id,
                transaction_features=decision.get("transaction_features", {}),
                graph_features=decision.get("graph_features", {}),
                decision=decision.get("decision", ""),
                combined_risk_score=decision.get("combined_risk_score", 0.0),
                ring_score=decision.get("ring_score", 0.0),
                override_triggered=decision.get("override_triggered", False)
            )
            
            logger.info(f"Processed decision {transaction_id}: {decision.get('decision')}")
            
            # If CHALLENGE, trigger step-up
            if decision.get("decision") == "CHALLENGE":
                self._trigger_step_up(transaction_id)
        
        except Exception as e:
            logger.error(f"Failed to process decision: {e}")
    
    def _trigger_step_up(self, transaction_id: str):
        """Trigger step-up. In production, call the OTP service."""
        logger.info(f"Step-up triggered for {transaction_id}")
        # Store step-up pending status
        from src.data.outcome_store import OutcomeStore
        store = OutcomeStore(self.store_path)
        data = store.get_decision(transaction_id)
        if data:
            store._load_store()
            # Step-up outcome will be recorded via API when completed

# For standalone execution
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    consumer = DecisionConsumer(
        store_path=os.getenv("STORE_PATH", "outcome_store.json"),
        model_path=os.getenv("MODEL_PATH", "models/tabular_model.pkl"),
        background_path=os.getenv("BACKGROUND_PATH", "models/background_data.pkl"),
        template_config_path=os.getenv("TEMPLATE_CONFIG_PATH", "config/templates/graph_reason_templates.yaml")
    )
    try:
        consumer.start()
    except KeyboardInterrupt:
        consumer.stop()