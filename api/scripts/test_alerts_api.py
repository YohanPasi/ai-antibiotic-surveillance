
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/stp/stage3"

def test_alerts_flow():
    print(f"Testing Alerts API at {BASE_URL}...")
    
    # 1. Get initial alerts
    resp = requests.get(f"{BASE_URL}/alerts")
    if resp.status_code != 200:
        print(f"FAILED to get alerts: {resp.status_code}")
        sys.exit(1)
        
    alerts = resp.json().get("alerts", [])
    print(f"Initial alert count: {len(alerts)}")
    
    if not alerts:
        print("No alerts to test dismissal on! (Is DB empty?)")
        # Try to inject one? No, assuming DB populated.
        sys.exit(1)
        
    target_alert = alerts[0]
    target_id = target_alert["id"]
    print(f"Targeting alert ID: {target_id} (Status: {target_alert['status']})")
    
    # 2. Dismiss it
    print(f"Dismissing alert {target_id}...")
    resp = requests.patch(f"{BASE_URL}/alerts/{target_id}/status?action=dismiss")
    if resp.status_code != 200:
        print(f"FAILED to dismiss: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    print("Dismiss success.")
    
    # 3. Verify it's gone
    print("Verifying persistence...")
    resp = requests.get(f"{BASE_URL}/alerts")
    new_alerts = resp.json().get("alerts", [])
    
    # Check if target_id exists in new_alerts
    found = any(a["id"] == target_id for a in new_alerts)
    
    if found:
        print("FAILED: Alert is STILL in the list after dismissal!")
        sys.exit(1)
    else:
        print("SUCCESS: Alert successfully removed from active view.")
        
if __name__ == "__main__":
    test_alerts_flow()
