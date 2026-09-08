import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.data.outcome_store import OutcomeStore

logger = logging.getLogger(__name__)

class GraphPrecisionMonitor:
    def __init__(self, store_path: str, alert_threshold: float = 0.15):
        self.store = OutcomeStore(store_path)
        self.alert_threshold = alert_threshold
    
    def get_ring_score_precision_signal(self, min_cases: int = 10) -> Dict:
        """Get precision signal for ring_score based on step-up completion."""
        store_data = self.store._load_store()
        
        # Filter to graph-driven challenges
        graph_challenges = {}
        for tx_id, data in store_data.items():
            if data.get("decision") != "CHALLENGE":
                continue
            if "step_up_result" not in data:
                continue
            
            # Check if graph reasons were present
            reasons = data.get("reasons", [])
            graph_reasons = [r for r in reasons if r.get("source") == "graph"]
            if not graph_reasons:
                continue
            
            ring_score = data.get("ring_score", 0)
            graph_challenges[tx_id] = {
                "ring_score": ring_score,
                "step_up_result": data["step_up_result"],
                "reasons": graph_reasons
            }
        
        if len(graph_challenges) < min_cases:
            return {"error": f"Insufficient data: {len(graph_challenges)} cases"}
        
        # Bucket by ring_score
        buckets = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
        bucket_data = {}
        
        for tx_id, data in graph_challenges.items():
            score = data["ring_score"]
            bucket_label = None
            for i in range(len(buckets) - 1):
                if buckets[i] <= score < buckets[i+1]:
                    bucket_label = f"{buckets[i]:.1f}-{buckets[i+1]:.1f}"
                    break
            if bucket_label is None:
                bucket_label = f"{buckets[-2]:.1f}+"
            
            if bucket_label not in bucket_data:
                bucket_data[bucket_label] = {"completed": 0, "abandoned": 0, "failed": 0}
            
            result = data["step_up_result"]
            if result in bucket_data[bucket_label]:
                bucket_data[bucket_label][result] += 1
        
        # Calculate rates
        result = {}
        for bucket_label, counts in bucket_data.items():
            total = counts["completed"] + counts["abandoned"] + counts["failed"]
            if total >= min_cases:
                result[bucket_label] = {
                    "total": total,
                    "completion_rate": round(counts["completed"] / total, 3) if total > 0 else 0,
                    "completed": counts["completed"]
                }
        
        return {
            "signal": "ring_score_precision",
            "buckets": result,
            "total_cases": len(graph_challenges),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def detect_precision_drift(self, window_days: int = 7) -> Dict:
        """Detect drift in graph model precision."""
        store_data = self.store._load_store()
        now = datetime.utcnow()
        cutoff = now - timedelta(days=window_days)
        
        # Get recent graph-driven challenges
        recent = []
        for tx_id, data in store_data.items():
            if data.get("decision") != "CHALLENGE":
                continue
            if "step_up_result" not in data:
                continue
            timestamp = data.get("step_up_timestamp")
            if not timestamp:
                continue
            dt = datetime.fromisoformat(timestamp)
            if dt < cutoff:
                continue
            
            reasons = data.get("reasons", [])
            graph_reasons = [r for r in reasons if r.get("source") == "graph"]
            if graph_reasons:
                recent.append(data["step_up_result"])
        
        if len(recent) < 10:
            return {"alert": False, "message": "Insufficient recent data"}
        
        completed = sum(1 for r in recent if r == "completed")
        rate = completed / len(recent) if recent else 0
        
        # Compare with historical baseline (all time)
        all_cases = []
        for tx_id, data in store_data.items():
            if data.get("decision") != "CHALLENGE":
                continue
            if "step_up_result" not in data:
                continue
            reasons = data.get("reasons", [])
            graph_reasons = [r for r in reasons if r.get("source") == "graph"]
            if graph_reasons:
                all_cases.append(data["step_up_result"])
        
        baseline_rate = sum(1 for r in all_cases if r == "completed") / len(all_cases) if all_cases else 0
        change = rate - baseline_rate
        
        alert = abs(change) > self.alert_threshold
        
        return {
            "alert": alert,
            "recent_rate": round(rate, 3),
            "baseline_rate": round(baseline_rate, 3),
            "change": round(change, 3),
            "recent_count": len(recent),
            "baseline_count": len(all_cases),
            "window_days": window_days,
            "threshold": self.alert_threshold,
            "message": f"Graph precision {'increased' if change > 0 else 'decreased'} by {abs(change):.1%}" if alert else "Stable"
        }
    
    def get_feedback_for_graph_model(self) -> Dict:
        """Generate feedback signal for graph model retraining."""
        # This is the signal to feed into the graph spec §2.8
        precision_signal = self.get_ring_score_precision_signal()
        drift = self.detect_precision_drift()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "precision_signal": precision_signal,
            "drift_detected": drift.get("alert", False),
            "drift_details": drift,
            "recommendation": self._get_recommendation(precision_signal, drift)
        }
    
    def _get_recommendation(self, precision_signal: Dict, drift: Dict) -> str:
        """Generate recommendation based on signals."""
        if drift.get("alert", False):
            if drift.get("change", 0) < 0:
                return "INVESTIGATE: Graph model precision decreasing. Review recent false positives."
            else:
                return "REVIEW: Graph model precision increasing. Verify signal is valid, not data issue."
        
        # Check bucket-specific issues
        buckets = precision_signal.get("buckets", {})
        for bucket_label, data in buckets.items():
            if data.get("completion_rate", 1) > 0.8:
                return f"REVIEW: High completion rate ({data['completion_rate']:.0%}) in bucket {bucket_label}. May indicate legitimate users being challenged."
        
        return "NORMAL: Graph model precision within expected range."