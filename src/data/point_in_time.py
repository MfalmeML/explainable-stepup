import json
import hashlib
from datetime import datetime
from typing import Dict, Any
from src.data.outcome_store import OutcomeStore

class PointInTimeRecorder:
    def __init__(self, store_path: str):
        self.store = OutcomeStore(store_path)
    
    def capture_decision_state(
        self,
        transaction_id: str,
        transaction_features: Dict[str, float],
        graph_features: Dict[str, float],
        decision: str,
        combined_risk_score: float,
        ring_score: float
    ) -> Dict:
        """Capture complete state at decision time for audit."""
        state = {
            "transaction_id": transaction_id,
            "decision": decision,
            "combined_risk_score": combined_risk_score,
            "ring_score": ring_score,
            "transaction_features": transaction_features,
            "graph_features": graph_features,
            "captured_at": datetime.utcnow().isoformat()
        }
        
        # Generate hash for integrity
        hash_input = json.dumps(state, sort_keys=True)
        state["state_hash"] = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Store in the outcome store
        store_data = self.store._load_store()
        if transaction_id not in store_data:
            store_data[transaction_id] = {}
        
        store_data[transaction_id]["point_in_time_state"] = state
        self.store._save_store(store_data)
        
        return state
    
    def get_decision_state(self, transaction_id: str) -> Dict:
        """Retrieve point-in-time state for a decision."""
        data = self.store.get_decision(transaction_id)
        if not data:
            return {"error": "Transaction not found"}
        
        state = data.get("point_in_time_state")
        if not state:
            return {"error": "Point-in-time state not captured"}
        
        # Verify integrity
        hash_input = json.dumps({
            k: v for k, v in state.items() if k != "state_hash"
        }, sort_keys=True)
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        if state.get("state_hash") != expected_hash:
            return {"error": "State integrity check failed - data may have been modified"}
        
        return state
    
    def freeze_graph_state(self, transaction_id: str) -> Dict:
        """Freeze graph state for later comparison."""
        state = self.get_decision_state(transaction_id)
        if "error" in state:
            return state
        
        # This would freeze the graph features at decision time
        # In practice, this would involve storing graph snapshot references
        
        return {
            "transaction_id": transaction_id,
            "graph_frozen": True,
            "frozen_at": datetime.utcnow().isoformat(),
            "features": state.get("graph_features", {})
        }