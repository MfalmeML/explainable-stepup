import random
import time
import requests
from datetime import datetime
from typing import Dict

def generate_step_up_event(transaction_id: str) -> Dict:
    """Simulate a step-up event from the OTP channel."""
    result = random.choices(
        ["completed", "abandoned", "failed"],
        weights=[0.7, 0.2, 0.1]
    )[0]
    
    latency = {
        "completed": random.randint(30000, 60000),
        "abandoned": random.randint(5000, 30000),
        "failed": random.randint(1000, 10000)
    }
    
    return {
        "transaction_id": transaction_id,
        "channel": "otp_sms",
        "result": result,
        "latency_ms": latency[result]
    }

def send_step_up_events(store_path: str, num_events: int = 10):
    """Generate and record step-up events for test transactions."""
    from src.data.outcome_store import OutcomeStore
    from src.validation.step_up_schema import StepUpRecord
    
    store = OutcomeStore(store_path)
    
    # Get all CHALLENGE transactions without step-up outcomes
    all_store = store._load_store()
    challenges = [
        tx_id for tx_id, data in all_store.items()
        if data.get("decision") == "CHALLENGE"
        and "step_up_result" not in data
    ]
    
    if not challenges:
        print("No CHALLENGE transactions found for step-up testing")
        return
    
    selected = random.sample(challenges, min(num_events, len(challenges)))
    
    for tx_id in selected:
        event = generate_step_up_event(tx_id)
        record = StepUpRecord(
            transaction_id=event["transaction_id"],
            channel=event["channel"],
            result=event["result"],
            latency_ms=event["latency_ms"]
        )
        success = store.record_step_up_outcome(record)
        print(f"{tx_id}: {event['result']} ({event['latency_ms']}ms) - {'Recorded' if success else 'Failed'}")
        time.sleep(0.1)