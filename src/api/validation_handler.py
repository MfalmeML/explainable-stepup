from src.validation.metrics import ValidationMetrics
from typing import Dict, Optional

class ValidationHandler:
    def __init__(self, store_path: str):
        self.metrics = ValidationMetrics(store_path)
    
    def handle_dashboard_stats(
        self,
        source: Optional[str] = None,
        min_cases: int = 5,
        days: int = 7
    ) -> Dict:
        """GET /validation/dashboard - Get complete validation dashboard data."""
        return {
            "completion_by_category": self.metrics.get_completion_rate_by_category(
                source=source,
                min_cases=min_cases
            ),
            "completion_by_ring_score": self.metrics.get_completion_rate_by_score_bucket(
                score_field="ring_score",
                min_cases=min_cases
            ),
            "trend_7d": self.metrics.get_trend_by_category(
                days=days,
                min_cases=min_cases
            ),
            "drift_alerts": self.metrics.detect_drift(
                threshold_change=0.15,
                window_days=1,
                min_cases=min_cases
            )
        }
    
    def handle_validation_stats(self, source: Optional[str] = None, min_cases: int = 5) -> Dict:
        """GET /validation/step-up-completion"""
        return {
            "reason_category_rates": self.metrics.get_completion_rate_by_category(
                source=source,
                min_cases=min_cases
            ),
            "source_filter": source or "all",
            "min_cases": min_cases
        }
    
    def handle_drift_check(self, threshold_change: float = 0.15) -> Dict:
        """GET /validation/drift - Check for drift in completion rates."""
        return {
            "drift_detected": self.metrics.detect_drift(
                threshold_change=threshold_change,
                window_days=1,
                min_cases=5
            )
        }