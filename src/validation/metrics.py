from src.data.outcome_store import OutcomeStore
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import json


def _parse_ts(ts_str: str) -> datetime:
    """Parse an ISO timestamp string, treating naive timestamps as UTC.

    step_up_timestamp values in the store may be naive (from older records,
    or any StepUpRecord created without an explicit timestamp) or
    timezone-aware (current default). Comparing a naive and an aware
    datetime raises TypeError, so every timestamp read from the store is
    normalized to aware-UTC here before it's used in any comparison.
    """
    dt = datetime.fromisoformat(ts_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

class ValidationMetrics:
    def __init__(self, store_path: str):
        self.store = OutcomeStore(store_path)
    
    def get_completion_rate_by_category(
        self,
        source: Optional[str] = None,
        min_cases: int = 5,
        time_window_hours: Optional[int] = None
    ) -> Dict[str, Dict]:
        """Get completion rate segmented by reason category."""
        return self.store.get_step_up_completion_rate_by_category(source, min_cases)
    
    def get_completion_rate_by_score_bucket(
        self,
        score_field: str = "ring_score",
        buckets: List[float] = [0.0, 0.3, 0.6, 0.8, 1.0],
        min_cases: int = 5
    ) -> Dict[str, Dict]:
        """Get completion rate segmented by score bucket."""
        store_data = self.store._load_store()
        
        # Filter to CHALLENGE decisions with step-up outcomes
        challenges = {
            tx_id: data
            for tx_id, data in store_data.items()
            if data.get("decision") == "CHALLENGE"
            and "step_up_result" in data
            and score_field in data
        }
        
        bucket_counts = {}
        for tx_id, data in challenges.items():
            score = data.get(score_field, 0.0)
            
            # Find bucket
            bucket_label = None
            for i in range(len(buckets) - 1):
                if buckets[i] <= score < buckets[i+1]:
                    bucket_label = f"{buckets[i]:.1f}-{buckets[i+1]:.1f}"
                    break
            if bucket_label is None:
                bucket_label = f"{buckets[-2]:.1f}+"
            
            if bucket_label not in bucket_counts:
                bucket_counts[bucket_label] = {"completed": 0, "abandoned": 0, "failed": 0}
            
            result = data["step_up_result"]
            if result in bucket_counts[bucket_label]:
                bucket_counts[bucket_label][result] += 1
        
        # Calculate rates and filter by min_cases
        result = {}
        for bucket_label, counts in bucket_counts.items():
            total = counts["completed"] + counts["abandoned"] + counts["failed"]
            if total >= min_cases:
                result[bucket_label] = {
                    "completed": counts["completed"],
                    "abandoned": counts["abandoned"],
                    "failed": counts["failed"],
                    "total": total,
                    "completion_rate": round(counts["completed"] / total, 3) if total > 0 else 0.0
                }
        
        return result
    
    def get_trend_by_category(
        self,
        days: int = 7,
        interval_hours: int = 24,
        min_cases: int = 3
    ) -> Dict[str, List[Dict]]:
        """Get completion rate trend over time by category."""
        store_data = self.store._load_store()
        
        # Filter to CHALLENGE with step-up outcomes
        challenges = {
            tx_id: data
            for tx_id, data in store_data.items()
            if data.get("decision") == "CHALLENGE"
            and "step_up_result" in data
            and "step_up_timestamp" in data
            and "reasons" in data
        }
        
        if not challenges:
            return {}
        
        # Determine time range
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        
        # Group by category and time interval
        categories = {}
        for tx_id, data in challenges.items():
            timestamp = _parse_ts(data["step_up_timestamp"])
            if timestamp < cutoff:
                continue
            
            # Determine category
            category = self.store._determine_category(data.get("reasons", []), None)
            if not category:
                category = "unknown"
            
            # Determine interval
            interval_key = timestamp.replace(
                minute=0, second=0, microsecond=0
            ) - timedelta(hours=timestamp.hour % interval_hours)
            interval_key = interval_key.isoformat()
            
            if category not in categories:
                categories[category] = {}
            
            if interval_key not in categories[category]:
                categories[category][interval_key] = {"completed": 0, "abandoned": 0, "failed": 0}
            
            result = data["step_up_result"]
            if result in categories[category][interval_key]:
                categories[category][interval_key][result] += 1
        
        # Build trend data
        result = {}
        for category, intervals in categories.items():
            trend = []
            for interval_key, counts in sorted(intervals.items()):
                total = counts["completed"] + counts["abandoned"] + counts["failed"]
                if total >= min_cases:
                    trend.append({
                        "timestamp": interval_key,
                        "completed": counts["completed"],
                        "abandoned": counts["abandoned"],
                        "failed": counts["failed"],
                        "total": total,
                        "completion_rate": round(counts["completed"] / total, 3) if total > 0 else 0.0
                    })
            if trend:
                result[category] = trend
        
        return result
    
    def detect_drift(
        self,
        threshold_change: float = 0.15,
        window_days: int = 1,
        min_cases: int = 5
    ) -> Dict[str, Dict]:
        """Detect significant changes in completion rates."""
        store_data = self.store._load_store()
        
        # Filter to CHALLENGE with step-up outcomes
        challenges = {
            tx_id: data
            for tx_id, data in store_data.items()
            if data.get("decision") == "CHALLENGE"
            and "step_up_result" in data
            and "step_up_timestamp" in data
            and "reasons" in data
        }
        
        if not challenges:
            return {}
        
        now = datetime.now(timezone.utc)
        cutoff_old = now - timedelta(days=window_days * 2)
        cutoff_new = now - timedelta(days=window_days)
        
        categories = {}
        for tx_id, data in challenges.items():
            timestamp = _parse_ts(data["step_up_timestamp"])
            
            if timestamp < cutoff_old:
                continue
            
            category = self.store._determine_category(data.get("reasons", []), None)
            if not category:
                category = "unknown"
            
            if category not in categories:
                categories[category] = {
                    "old": {"completed": 0, "abandoned": 0, "failed": 0},
                    "new": {"completed": 0, "abandoned": 0, "failed": 0}
                }
            
            period = "old" if timestamp < cutoff_new else "new"
            result = data["step_up_result"]
            if result in categories[category][period]:
                categories[category][period][result] += 1
        
        # Calculate drift
        result = {}
        for category, periods in categories.items():
            old_total = periods["old"]["completed"] + periods["old"]["abandoned"] + periods["old"]["failed"]
            new_total = periods["new"]["completed"] + periods["new"]["abandoned"] + periods["new"]["failed"]
            
            if old_total < min_cases or new_total < min_cases:
                continue
            
            old_rate = periods["old"]["completed"] / old_total if old_total > 0 else 0
            new_rate = periods["new"]["completed"] / new_total if new_total > 0 else 0
            
            change = new_rate - old_rate
            if abs(change) >= threshold_change:
                result[category] = {
                    "old_rate": round(old_rate, 3),
                    "new_rate": round(new_rate, 3),
                    "change": round(change, 3),
                    "old_count": old_total,
                    "new_count": new_total,
                    "direction": "up" if change > 0 else "down",
                    "alert": True
                }
        
        return result