import json
import csv
from datetime import datetime
from typing import Dict, List
from src.data.outcome_store import OutcomeStore

class ComplianceExport:
    def __init__(self, store_path: str):
        self.store = OutcomeStore(store_path)
    
    def export_adverse_action(self, transaction_id: str) -> Dict:
        """Generate compliance-ready adverse action justification."""
        data = self.store.get_decision(transaction_id)
        if not data:
            return {"error": "Transaction not found"}
        
        if data.get("decision") == "APPROVE":
            return {"error": "No adverse action for APPROVE decisions"}
        
        reasons = data.get("reasons", [])
        
        # Build written justification
        if data.get("override_driven", False):
            justification = "Declined due to confirmed fraud ring membership. This decision was based on network analysis indicating connection to known fraudulent activity."
        else:
            reason_texts = [r.get("text", "") for r in reasons[:3]]
            if reason_texts:
                justification = f"Decision based on: {', '.join(reason_texts)}."
            else:
                justification = "Decision based on risk score assessment."
        
        return {
            "transaction_id": transaction_id,
            "decision": data.get("decision"),
            "decision_timestamp": data.get("decision_timestamp"),
            "combined_risk_score": data.get("combined_risk_score"),
            "reasons": reasons,
            "override_driven": data.get("override_driven", False),
            "justification": justification,
            "template_version": data.get("reason_template_version"),
            "export_timestamp": datetime.utcnow().isoformat()
        }
    
    def export_all_adverse_actions(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """Export all adverse action records for compliance review."""
        store_data = self.store._load_store()
        
        exports = []
        for tx_id, data in store_data.items():
            if data.get("decision") in ["CHALLENGE", "DECLINE"]:
                export = self.export_adverse_action(tx_id)
                if "error" not in export:
                    exports.append(export)
        
        return exports
    
    def export_to_csv(self, output_path: str):
        """Export adverse actions to CSV for compliance team."""
        exports = self.export_all_adverse_actions()
        
        if not exports:
            print("No adverse actions to export")
            return
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'transaction_id', 'decision', 'decision_timestamp',
                'combined_risk_score', 'justification', 'override_driven',
                'template_version'
            ])
            writer.writeheader()
            for export in exports:
                writer.writerow({
                    'transaction_id': export['transaction_id'],
                    'decision': export['decision'],
                    'decision_timestamp': export['decision_timestamp'],
                    'combined_risk_score': export['combined_risk_score'],
                    'justification': export['justification'],
                    'override_driven': export['override_driven'],
                    'template_version': export['template_version']
                })
        
        print(f"Exported {len(exports)} records to {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python compliance_export.py <store_path> <output.csv>")
        sys.exit(1)
    
    exporter = ComplianceExport(sys.argv[1])
    exporter.export_to_csv(sys.argv[2])