import json
from typing import Dict, List, Optional
from datetime import datetime

class InvestigatorView:
    def __init__(self, outcome_store_path: str):
        self.outcome_store_path = outcome_store_path
    
    def get_case_detail(self, transaction_id: str) -> Dict:
        """Retrieve case detail with reason codes for investigator."""
        # In production, this would query a database
        # For now, load from a JSON file store
        try:
            with open(self.outcome_store_path, 'r') as f:
                store = json.load(f)
        except FileNotFoundError:
            return {"error": "Case not found"}
        
        case = store.get(transaction_id)
        if not case:
            return {"error": "Case not found"}
        
        return {
            "transaction_id": transaction_id,
            "decision": case.get("decision"),
            "combined_risk_score": case.get("combined_risk_score"),
            "reasons": case.get("reasons", []),
            "override_driven": case.get("override_driven", False),
            "reason_template_version": case.get("reason_template_version")
        }
    
    def record_reason_agreement(
        self, 
        transaction_id: str, 
        investigator_id: str,
        agreement: bool,
        notes: Optional[str] = None
    ) -> Dict:
        """Record investigator's agreement/disagreement with surfaced reasons."""
        try:
            with open(self.outcome_store_path, 'r') as f:
                store = json.load(f)
        except FileNotFoundError:
            return {"error": "Case not found"}
        
        if transaction_id not in store:
            return {"error": "Case not found"}
        
        # Record agreement
        store[transaction_id]["reason_agreement"] = 1 if agreement else 0
        store[transaction_id]["investigator_id"] = investigator_id
        store[transaction_id]["investigator_review_timestamp"] = datetime.utcnow().isoformat()
        if notes:
            store[transaction_id]["investigator_notes"] = notes
        
        # Write back
        with open(self.outcome_store_path, 'w') as f:
            json.dump(store, f, indent=2)
        
        return {"status": "recorded", "agreement": agreement}
    
    def get_review_sample(self, sample_size: int = 10) -> List[Dict]:
        """Retrieve a sample of cases needing investigator review."""
        try:
            with open(self.outcome_store_path, 'r') as f:
                store = json.load(f)
        except FileNotFoundError:
            return []
        
        # Find cases that haven't been reviewed
        unreviewed = []
        for tx_id, case in store.items():
            if "reason_agreement" not in case and case.get("decision") != "APPROVE":
                unreviewed.append({
                    "transaction_id": tx_id,
                    "decision": case.get("decision"),
                    "combined_risk_score": case.get("combined_risk_score"),
                    "reasons": case.get("reasons", [])
                })
        
        return unreviewed[:sample_size]