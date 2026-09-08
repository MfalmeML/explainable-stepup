import json
import sys
import requests
import time

def verify_all_components(base_url: str = "http://localhost:5000"):
    """Verify all components are working."""
    print("\n=== Complete System Verification ===\n")
    
    checks = []
    
    # 1. API health
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        checks.append(("API Health", r.status_code == 200, str(r.status_code)))
    except Exception as e:
        checks.append(("API Health", False, str(e)))
    
    # 2. Coverage metrics
    try:
        r = requests.get(f"{base_url}/metrics/coverage", timeout=5)
        checks.append(("Coverage Metrics", r.status_code == 200, str(r.status_code)))
    except Exception as e:
        checks.append(("Coverage Metrics", False, str(e)))
    
    # 3. Validation dashboard
    try:
        r = requests.get(f"{base_url}/validation/dashboard", timeout=5)
        checks.append(("Validation Dashboard", r.status_code == 200, str(r.status_code)))
    except Exception as e:
        checks.append(("Validation Dashboard", False, str(e)))
    
    # 4. Drift detection
    try:
        r = requests.get(f"{base_url}/validation/drift", timeout=5)
        checks.append(("Drift Detection", r.status_code == 200, str(r.status_code)))
    except Exception as e:
        checks.append(("Drift Detection", False, str(e)))
    
    # 5. MLOps metrics
    try:
        r = requests.get(f"{base_url}/metrics/dashboard", timeout=5)
        checks.append(("MLOps Dashboard", r.status_code == 200, str(r.status_code)))
    except Exception as e:
        checks.append(("MLOps Dashboard", False, str(e)))
    
    # Print results
    print("Component Verification Results:")
    print("-" * 50)
    for name, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{name:30} {status} ({detail})")
    print("-" * 50)
    
    # Overall status
    all_passed = all(passed for _, passed, _ in checks)
    print(f"\nOverall Status: {'COMPLETE' if all_passed else 'INCOMPLETE'}")
    
    return all_passed

if __name__ == "__main__":
    success = verify_all_components()
    sys.exit(0 if success else 1)