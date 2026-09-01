import json
import random
from datetime import datetime, timedelta

def initialize_outcome_store(path: str, num_cases: int = 20):
    """Initialize a sample outcome store for testing."""
    store = {}
    
    decisions = ["CHALLENGE", "DECLINE", "APPROVE"]
    reason_templates = [
        "Transaction amount 8.2x normal",
        "New device",
        "Device linked to 4 other accounts",
        "Account is 1 hops from confirmed fraud device",
        "Part of connected fraud network with 12 accounts",
        "Velocity exceeds threshold",
        "IP address mismatch"
    ]
    
    for i in range(num_cases):
        tx_id = f"tx_{10000 + i}"
        decision = random.choice(decisions)
        
        case = {
            "transaction_id": tx_id,
            "decision": decision,
            "combined_risk_score": round(random.uniform(0.1, 0.95), 2),
            "ring_score": round(random.uniform(0, 0.9), 2),
            "reason_template_version": "2026-08-30-v1",
            "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat()
        }
        
        if decision != "APPROVE":
            # Generate 1-3 reasons
            num_reasons = random.randint(1, 3)
            reasons = []
            sources = ["tabular", "graph"]
            for _ in range(num_reasons):
                reasons.append({
                    "text": random.choice(reason_templates),
                    "source": random.choice(sources),
                    "weight": round(random.uniform(0.1, 0.9), 2)
                })
            case["reasons"] = reasons
            case["override_driven"] = random.choice([True, False]) if decision == "DECLINE" else False
            
            # Randomly mark some as already reviewed
            if random.random() > 0.5:
                case["reason_agreement"] = random.choice([0, 1])
                case["investigator_id"] = f"inv_{random.randint(1, 5)}"
        
        store[tx_id] = case
    
    with open(path, 'w') as f:
        json.dump(store, f, indent=2)
    
    return store