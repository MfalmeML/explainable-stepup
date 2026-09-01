import json
import sys
from src.ui.investigator_view import InvestigatorView

def print_case(case):
    """Pretty print a case for investigator review."""
    print("\n" + "="*60)
    print(f"Transaction: {case.get('transaction_id')}")
    print(f"Decision: {case.get('decision')}")
    print(f"Risk Score: {case.get('combined_risk_score')}")
    print(f"Override Driven: {case.get('override_driven', False)}")
    print("\nReason Codes:")
    for idx, reason in enumerate(case.get('reasons', []), 1):
        print(f"  {idx}. [{reason.get('source')}] {reason.get('text')} (weight: {reason.get('weight')})")
    print("="*60)

def main():
    store_path = "outcome_store.json"
    view = InvestigatorView(store_path)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py sample [count]   - Show unreviewed cases")
        print("  python cli.py view <tx_id>     - View a specific case")
        print("  python cli.py agree <tx_id>    - Mark case as agreed")
        print("  python cli.py disagree <tx_id> - Mark case as disagreed")
        return
    
    command = sys.argv[1]
    
    if command == "sample":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        sample = view.get_review_sample(count)
        print(f"Found {len(sample)} unreviewed cases")
        for case in sample:
            print_case(case)
            print("\nTo review: python cli.py view {tx_id}")
    
    elif command == "view" and len(sys.argv) > 2:
        case = view.get_case_detail(sys.argv[2])
        if "error" in case:
            print(case["error"])
        else:
            print_case(case)
            print("\nCommands:")
            print(f"  python cli.py agree {sys.argv[2]}")
            print(f"  python cli.py disagree {sys.argv[2]}")
    
    elif command == "agree" and len(sys.argv) > 2:
        result = view.record_reason_agreement(sys.argv[2], "cli_investigator", True)
        print(result)
    
    elif command == "disagree" and len(sys.argv) > 2:
        result = view.record_reason_agreement(sys.argv[2], "cli_investigator", False)
        print(result)
    
    else:
        print("Unknown command or missing arguments")

if __name__ == "__main__":
    main()