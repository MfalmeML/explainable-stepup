import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MLOpsMonitor:
    def __init__(self, store_path: str):
        self.store_path = store_path
    
    def _load_store(self) -> Dict:
        try:
            with open(self.store_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_explanation_coverage(self) -> Dict:
        """Reason-code coverage metric."""
        store = self._load_store()
        total = len(store)
        
        non_approve = 0
        with_explanation = 0
        degraded = 0
        
        for tx_id, data in store.items():
            if data.get("decision") != "APPROVE":
                non_approve += 1
                if "reasons" in data and data["reasons"]:
                    with_explanation += 1
                if data.get("degraded", False):
                    degraded += 1
        
        return {
            "total_decisions": total,
            "non_approve_decisions": non_approve,
            "with_explanation": with_explanation,
            "degraded_explanations": degraded,
            "coverage_rate": round(with_explanation / non_approve, 3) if non_approve > 0 else 0,
            "degraded_rate": round(degraded / non_approve, 3) if non_approve > 0 else 0
        }
    
    def get_reason_distribution(self, days: Optional[int] = None) -> Dict[str, int]:
        """Explanation drift monitoring - distribution of reason codes."""
        store = self._load_store()
        
        cutoff = None
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
        
        reason_counter = Counter()
        
        for tx_id, data in store.items():
            if cutoff:
                timestamp = data.get("decision_timestamp")
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    if dt < cutoff:
                        continue
            
            for reason in data.get("reasons", []):
                text = reason.get("text", "")
                # Normalize reason text
                if "device" in text.lower():
                    key = "new_device"
                elif "fraud ring" in text.lower() or "confirmed fraud" in text.lower():
                    key = "fraud_ring"
                elif "network" in text.lower() or "connected" in text.lower():
                    key = "network"
                elif "amount" in text.lower() or "normal" in text.lower():
                    key = "amount_anomaly"
                elif "velocity" in text.lower():
                    key = "velocity"
                elif "ip" in text.lower():
                    key = "ip_mismatch"
                else:
                    key = "other"
                reason_counter[key] += 1
        
        return dict(reason_counter)
    
    def get_faithfulness_stats(self) -> Dict:
        """Faithfulness monitoring results."""
        store = self._load_store()
        
        total_checked = 0
        passed = 0
        failed = 0
        
        for tx_id, data in store.items():
            if "faithfulness_checked" in data:
                total_checked += 1
                if data.get("faithfulness_passed", False):
                    passed += 1
                else:
                    failed += 1
        
        return {
            "total_checked": total_checked,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total_checked, 3) if total_checked > 0 else 0
        }
    
    def get_mlops_dashboard(self) -> Dict:
        """Complete MLOps dashboard."""
        return {
            "coverage": self.get_explanation_coverage(),
            "reason_distribution": self.get_reason_distribution(days=7),
            "faithfulness": self.get_faithfulness_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }