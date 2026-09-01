import json
import os
from typing import Optional, Dict, List
from datetime import datetime
from src.validation.step_up_schema import StepUpRecord, StepUpResult

class OutcomeStore:
    def __init__(self, store_path: str):
        self.store_path = store_path
        self._ensure_store_exists()
    
    def _ensure_store_exists(self):
        if not os.path.exists(self.store_path):
            with open(self.store_path, 'w') as f:
                json.dump({}, f)
    
    def _load_store(self) -> Dict:
        with open(self.store_path, 'r') as f:
            return json.load(f)
    
    def _save_store(self, store: Dict):
        with open(self.store_path, 'w') as f:
            json.dump(store, f, indent=2)
    
    def get_decision(self, transaction_id: str) -> Optional[Dict]:
        store = self._load_store()
        return store.get(transaction_id)
    
    def save_decision_record(
        self,
        transaction_id: str,
        decision: str,
        combined_risk_score: float,
        ring_score: float,
        reasons: List[Dict],
        override_driven: bool,
        reason_template_version: str
    ):
        store = self._load_store()
        store[transaction_id] = {
            "transaction_id": transaction_id,
            "decision": decision,
            "combined_risk_score": combined_risk_score,
            "ring_score": ring_score,
            "reasons": reasons,
            "override_driven": override_driven,
            "reason_template_version": reason_template_version,
            "decision_timestamp": datetime.utcnow().isoformat()
        }
        self._save_store(store)
    
    def record_step_up_outcome(self, step_up_record: StepUpRecord) -> bool:
        store = self._load_store()
        tx_id = step_up_record.transaction_id
        
        if tx_id not in store:
            return False
        
        store[tx_id]["step_up_result"] = step_up_record.result
        store[tx_id]["step_up_channel"] = step_up_record.channel
        store[tx_id]["step_up_latency_ms"] = step_up_record.latency_ms
        store[tx_id]["step_up_timestamp"] = step_up_record.timestamp
        
        self._save_store(store)
        return True
    
    def get_step_up_completion_rate_by_category(
        self,
        source: Optional[str] = None,
        min_cases: int = 5
    ) -> Dict[str, Dict]:
        """
        Compute completion rate segmented by reason category.
        Returns: {category: {"completed": n, "total": n, "rate": float}}
        """
        store = self._load_store()
        
        # Filter to CHALLENGE decisions with step-up outcomes
        challenges = {
            tx_id: data 
            for tx_id, data in store.items() 
            if data.get("decision") == "CHALLENGE" 
            and "step_up_result" in data
            and "reasons" in data
        }
        
        categories = {}
        for tx_id, data in challenges.items():
            # Determine category from reasons
            category = self._determine_category(data.get("reasons", []), source)
            if not category:
                continue
            
            if category not in categories:
                categories[category] = {"completed": 0, "abandoned": 0, "failed": 0}
            
            result = data["step_up_result"]
            if result in categories[category]:
                categories[category][result] += 1
        
        # Calculate rates and filter by min_cases
        result = {}
        for category, counts in categories.items():
            total = counts["completed"] + counts["abandoned"] + counts["failed"]
            if total >= min_cases:
                result[category] = {
                    "completed": counts["completed"],
                    "abandoned": counts["abandoned"],
                    "failed": counts["failed"],
                    "total": total,
                    "completion_rate": round(counts["completed"] / total, 3) if total > 0 else 0.0
                }
        
        return result
    
    def _determine_category(self, reasons: List[Dict], source: Optional[str] = None) -> str:
        """Determine the primary category from reason list."""
        if not reasons:
            return "unknown"
        
        # Filter by source if specified
        if source:
            reasons = [r for r in reasons if r.get("source") == source]
        
        if not reasons:
            return "unknown"
        
        # Use the highest weight reason as the category
        primary = max(reasons, key=lambda x: x.get("weight", 0))
        text = primary.get("text", "")
        
        # Map to categories
        if "device" in text.lower():
            return "new_device"
        elif "fraud ring" in text.lower() or "confirmed fraud" in text.lower():
            return "fraud_ring"
        elif "network" in text.lower() or "connected" in text.lower():
            return "network"
        elif "amount" in text.lower() or "normal" in text.lower():
            return "amount_anomaly"
        elif "velocity" in text.lower():
            return "velocity"
        elif "ip" in text.lower():
            return "ip_mismatch"
        else:
            return "other"