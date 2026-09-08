from typing import Dict, List, Optional

class CustomerMessageFilter:
    """Filter reason codes for customer-facing disclosure (policy-gated)."""
    
    # Reasons safe for external disclosure
    ALLOWED_REASON_PATTERNS = [
        "amount", "normal", "unusual",
        "device", "new device",
        "velocity", "too many",
        "ip", "mismatch",
        "location"
    ]
    
    # Reasons NOT safe for external disclosure (internal only)
    BLOCKED_REASON_PATTERNS = [
        "fraud ring",
        "confirmed fraud",
        "network",
        "connected fraud",
        "override"
    ]
    
    @classmethod
    def filter_for_customer(cls, reasons: List[Dict]) -> List[Dict]:
        """Filter reasons for customer-facing display."""
        if not reasons:
            return []
        
        filtered = []
        for reason in reasons:
            text = reason.get('text', '').lower()
            
            # Check if blocked
            blocked = any(pattern in text for pattern in cls.BLOCKED_REASON_PATTERNS)
            if blocked:
                continue
            
            # Check if allowed
            allowed = any(pattern in text for pattern in cls.ALLOWED_REASON_PATTERNS)
            if allowed:
                filtered.append(reason)
        
        # If no reasons remain, provide generic message
        if not filtered:
            return [{
                "text": "Transaction did not meet our risk criteria",
                "source": "generic",
                "weight": 0.0
            }]
        
        return filtered
    
    @classmethod
    def get_customer_message(cls, reasons: List[Dict]) -> str:
        """Get formatted customer message."""
        filtered = cls.filter_for_customer(reasons)
        if not filtered:
            return "Your transaction was flagged for additional verification."
        
        messages = [r.get('text', '') for r in filtered[:2]]
        return f"Your transaction was flagged due to: {', '.join(messages)}."

# Test
if __name__ == "__main__":
    test_reasons = [
        {"text": "Transaction amount 8.2x normal", "source": "tabular", "weight": 0.5},
        {"text": "New device", "source": "tabular", "weight": 0.4},
        {"text": "Linked to confirmed fraud ring", "source": "graph", "weight": 0.9}
    ]
    
    print("Original:", test_reasons)
    print("Customer:", CustomerMessageFilter.filter_for_customer(test_reasons))
    print("Message:", CustomerMessageFilter.get_customer_message(test_reasons))