from typing import Dict

from src.ui.investigator_view import InvestigatorView


class APIHandlers:
    """Application handlers shared by the HTTP API and production runner."""

    def __init__(self, store_path: str):
        self.investigator_view = InvestigatorView(store_path)

    def handle_get_case(self, transaction_id: str) -> Dict:
        return self.investigator_view.get_case_detail(transaction_id)

    def handle_post_agreement(self, payload: Dict) -> Dict:
        required = ["transaction_id", "investigator_id", "agreement"]
        for field in required:
            if field not in payload:
                return {"error": f"Missing field: {field}"}

        return self.investigator_view.record_reason_agreement(
            transaction_id=payload["transaction_id"],
            investigator_id=payload["investigator_id"],
            agreement=bool(payload["agreement"]),
            notes=payload.get("notes")
        )

    def handle_get_sample(self, sample_size: int = 10) -> Dict:
        if sample_size < 1:
            return {"error": "size must be greater than zero"}
        return {
            "sample_size": sample_size,
            "cases": self.investigator_view.get_review_sample(sample_size)
        }
