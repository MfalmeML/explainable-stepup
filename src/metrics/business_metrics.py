import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BusinessMetrics:
    def __init__(self, store_path: str):
        self.store_path = store_path
    
    def _load_store(self) -> Dict:
        try:
            with open(self.store_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_investigator_time_saved(self, time_window_days: int = 30) -> Dict:
        """Estimate investigator time saved by reason codes."""
        store = self._load_store()
        now = datetime.utcnow()
        cutoff = now - timedelta(days=time_window_days)
        
        # Count non-approve decisions with reasons
        total_cases = 0
        with_reasons = 0
        
        for tx_id, data in store.items():
            timestamp = data.get("decision_timestamp")
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                if dt < cutoff:
                    continue
            
            if data.get("decision") != "APPROVE":
                total_cases += 1
                if data.get("reasons") and len(data.get("reasons", [])) > 0:
                    with_reasons += 1
        
        # Assumption: reasons save 2 minutes per case
        time_saved_per_case_minutes = 2
        time_saved_hours = (with_reasons * time_saved_per_case_minutes) / 60
        
        return {
            "time_window_days": time_window_days,
            "total_non_approve_cases": total_cases,
            "cases_with_reasons": with_reasons,
            "coverage_rate": round(with_reasons / total_cases, 3) if total_cases > 0 else 0,
            "estimated_time_saved_hours": round(time_saved_hours, 2),
            "estimated_time_saved_minutes": round(time_saved_minutes, 2) if 'time_saved_minutes' in locals() else 0
        }
    
    def get_dispute_resolution_time_impact(self, time_window_days: int = 30) -> Dict:
        """Measure dispute resolution time impact."""
        store = self._load_store()
        
        # This requires integration with the dispute system
        # For now, return structure based on available data
        
        return {
            "time_window_days": time_window_days,
            "status": "requires_dispute_system_integration",
            "available_metrics": [
                "time_to_resolution_baseline",
                "time_to_resolution_with_explanations",
                "reduction_percentage"
            ]
        }
    
    def get_regulatory_risk_reduction(self) -> Dict:
        """Estimate regulatory risk reduction."""
        store = self._load_store()
        
        # Count adverse actions with proper justifications
        adverse_actions = 0
        with_justification = 0
        
        for tx_id, data in store.items():
            if data.get("decision") in ["DECLINE", "CHALLENGE"]:
                adverse_actions += 1
                if data.get("reasons") and len(data.get("reasons", [])) > 0:
                    with_justification += 1
        
        return {
            "total_adverse_actions": adverse_actions,
            "with_written_justification": with_justification,
            "coverage_rate": round(with_justification / adverse_actions, 3) if adverse_actions > 0 else 0,
            "risk_mitigation": "High" if with_justification > 0.9 * adverse_actions else "Medium" if with_justification > 0.5 * adverse_actions else "Low",
            "regulatory_compliance": "Defensible" if with_justification > 0.9 * adverse_actions else "At Risk"
        }
    
    def get_infrastructure_cost(self) -> Dict:
        """Track explanation infrastructure cost."""
        store = self._load_store()
        total_explanations = sum(1 for data in store.values() if data.get("reasons"))
        
        # Estimate costs
        # SHAP compute: ~0.01 per explanation
        # Storage: ~$0.0001 per record
        # API: ~$0.001 per request
        
        shap_cost = total_explanations * 0.01
        storage_cost = len(store) * 0.0001
        api_cost = total_explanations * 0.001
        
        return {
            "total_explanations": total_explanations,
            "total_records": len(store),
            "estimated_shap_compute_cost_usd": round(shap_cost, 2),
            "estimated_storage_cost_usd": round(storage_cost, 2),
            "estimated_api_cost_usd": round(api_cost, 2),
            "total_estimated_cost_usd": round(shap_cost + storage_cost + api_cost, 2)
        }
    
    def get_business_impact_dashboard(self, time_window_days: int = 30) -> Dict:
        """Complete business impact dashboard."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_window_days": time_window_days,
            "investigator_impact": self.get_investigator_time_saved(time_window_days),
            "regulatory_impact": self.get_regulatory_risk_reduction(),
            "infrastructure_cost": self.get_infrastructure_cost(),
            "quality_metrics": self._get_quality_metrics()
        }
    
    def _get_quality_metrics(self) -> Dict:
        """Get quality metrics from the system."""
        store = self._load_store()
        
        total_reviewed = 0
        agreed = 0
        
        for tx_id, data in store.items():
            if "reason_agreement" in data:
                total_reviewed += 1
                if data["reason_agreement"] == 1:
                    agreed += 1
        
        return {
            "investigator_agreement_rate": round(agreed / total_reviewed, 3) if total_reviewed > 0 else 0,
            "total_reviewed": total_reviewed,
            "total_agreed": agreed,
            "faithfulness_pass_rate": self._get_faithfulness_pass_rate()
        }
    
    def _get_faithfulness_pass_rate(self) -> float:
        """Get faithfulness pass rate from stored checks."""
        store = self._load_store()
        
        total_checked = 0
        passed = 0
        
        for tx_id, data in store.items():
            if data.get("faithfulness_checked", False):
                total_checked += 1
                if data.get("faithfulness_passed", False):
                    passed += 1
        
        return round(passed / total_checked, 3) if total_checked > 0 else 0