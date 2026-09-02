import json
import random
import time
import os
from datetime import datetime

def produce_decision(queue_path: str = "/tmp/decision_queue.jsonl"):
    """Generate and enqueue sample decisions."""
    os.makedirs(os.path.dirname(queue_path), exist_ok=True)
    
    decisions = ["APPROVE", "CHALLENGE", "DECLINE"]
    weights = [0.6, 0.3, 0.1]
    
    for i in range(20):
        decision = random.choices(decisions, weights=weights)[0]
        
        # Generate realistic features
        amount = random.uniform(10, 5000)
        device_count = random.poisson(2)
        age_days = random.exponential(365)
        velocity_1h = random.poisson(1)
        
        # Make some suspicious
        if decision in ["CHALLENGE", "DECLINE"]:
            amount = random.uniform(500, 10000)
            device_count = random.poisson(5)
            age_days = random.exponential(30)
            velocity_1h = random.poisson(3)
        
        transaction = {
            "transaction_id": f"tx_{int(time.time() * 1000)}_{i}",
            "decision": decision,
            "combined_risk_score": random.uniform(0.1, 0.95),
            "ring_score": random.uniform(0, 0.9) if decision != "APPROVE" else random.uniform(0, 0.3),
            "override_triggered": random.random() < 0.05 and decision == "DECLINE",
            "transaction_features": {
                "amount": round(amount, 2),
                "device_count": device_count,
                "age_days": round(age_days, 0),
                "velocity_1h": velocity_1h,
                "velocity_24h": velocity_1h * random.uniform(5, 15),
                "ip_match": 1 if random.random() > 0.2 else 0,
                "country_match": 1 if random.random() > 0.1 else 0,
                "session_duration": random.exponential(600),
                "payment_method_age": random.exponential(365),
                "failed_attempts": random.poisson(0.2)
            },
            "graph_features": {
                "device_account_count": random.poisson(3) + (3 if decision != "APPROVE" else 0),
                "shortest_path_to_confirmed_fraud": random.poisson(2) if decision != "APPROVE" else 10,
                "connected_component_size": random.poisson(5) if decision != "APPROVE" else 1,
                "new_edges_last_1h": random.poisson(1) if decision != "APPROVE" else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with open(queue_path, 'a') as f:
            f.write(json.dumps(transaction) + '\n')
        
        print(f"Enqueued: {transaction['transaction_id']} - {decision}")
        time.sleep(0.1)

if __name__ == "__main__":
    produce_decision()