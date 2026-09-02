from typing import Literal, Optional
from datetime import datetime, timezone

StepUpResult = Literal["completed", "abandoned", "failed"]

class StepUpRecord:
    def __init__(
        self,
        transaction_id: str,
        channel: str,
        result: StepUpResult,
        latency_ms: int,
        timestamp: Optional[str] = None
    ):
        self.transaction_id = transaction_id
        self.channel = channel
        self.result = result
        self.latency_ms = latency_ms
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "step_up_channel": self.channel,
            "step_up_result": self.result,
            "step_up_latency_ms": self.latency_ms,
            "timestamp": self.timestamp
        }