from src.data.outcome_store import OutcomeStore
from src.validation.step_up_schema import StepUpRecord
from typing import Dict

class StepUpHandler:
    def __init__(self, store_path: str):
        self.store = OutcomeStore(store_path)
    
    def handle_step_up_capture(self, payload: Dict) -> Dict:
        """POST /step-up-outcome"""
        required = ["transaction_id", "channel", "result", "latency_ms"]
        for field in required:
            if field not in payload:
                return {"error": f"Missing field: {field}"}
        
        # Validate result
        valid_results = ["completed", "abandoned", "failed"]
        if payload["result"] not in valid_results:
            return {"error": f"Invalid result. Must be one of: {valid_results}"}
        
        record = StepUpRecord(
            transaction_id=payload["transaction_id"],
            channel=payload["channel"],
            result=payload["result"],
            latency_ms=payload["latency_ms"]
        )
        
        success = self.store.record_step_up_outcome(record)
        if not success:
            return {"error": "Transaction not found"}
        
        return {"status": "recorded", "transaction_id": payload["transaction_id"]}
    
    def handle_validation_stats(self, source: str = None, min_cases: int = 5) -> Dict:
        """GET /validation/step-up-completion"""
        rates = self.store.get_step_up_completion_rate_by_category(source, min_cases)
        return {
            "reason_category_rates": rates,
            "source_filter": source or "all",
            "min_cases": min_cases
        }