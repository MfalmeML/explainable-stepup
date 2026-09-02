import sys
import json
import requests
import time

def verify_api(base_url: str = "http://localhost:5000"):
    """Verify all API endpoints are working."""
    print(f"Verifying API at {base_url}")
    
    tests = []
    
    # Health check
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        if r.status_code == 200:
            tests.append(("Health", "PASS"))
        else:
            tests.append(("Health", f"FAIL: {r.status_code}"))
    except Exception as e:
        tests.append(("Health", f"FAIL: {e}"))
    
    # Coverage
    try:
        r = requests.get(f"{base_url}/metrics/coverage", timeout=5)
        if r.status_code == 200:
            tests.append(("Coverage", "PASS"))
        else:
            tests.append(("Coverage", f"FAIL: {r.status_code}"))
    except Exception as e:
        tests.append(("Coverage", f"FAIL: {e}"))
    
    # Validation dashboard
    try:
        r = requests.get(f"{base_url}/validation/dashboard", timeout=5)
        if r.status_code == 200:
            tests.append(("Dashboard", "PASS"))
        else:
            tests.append(("Dashboard", f"FAIL: {r.status_code}"))
    except Exception as e:
        tests.append(("Dashboard", f"FAIL: {e}"))
    
    print("\nVerification Results:")
    print("-" * 50)
    for name, status in tests:
        print(f"{name:20} {status}")
    print("-" * 50)
    
    failed = any("FAIL" in status for _, status in tests)
    return not failed

if __name__ == "__main__":
    success = verify_api()
    sys.exit(0 if success else 1)