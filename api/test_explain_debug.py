import urllib.request
import json
import ssl
import sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# CONFIG
url_login = "http://localhost:8000/api/auth/token"
url_predict = "http://localhost:8000/api/mrsa/predict"

login_payload = "username=admin&password=Password123"

# DATA
payload = {
    "age": 65,
    "gender": "Male",
    "ward": "ICU",
    "sample_type": "Blood",
    "pus_type": "Unknown",
    "cell_count": 0,
    "gram_positivity": "GPC",
    "growth_time": 24.0,
    "bht": "Unknown"
}

try:
    print("Logging in as admin...")
    auth_req = urllib.request.Request(
        url_login, 
        data=login_payload.encode(), 
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with urllib.request.urlopen(auth_req, context=ctx) as response:
        token_data = json.loads(response.read().decode())
    
    token = token_data['access_token']
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    print("Login success.")

    print(f"Predicting with Ward: {payload['ward']}...")
    pred_req = urllib.request.Request(
        url_predict, 
        data=json.dumps(payload).encode(), 
        headers=headers
    )
    with urllib.request.urlopen(pred_req, context=ctx) as response:
        pred = json.loads(response.read().decode())
        aid = pred['assessment_id']
        print(f"Prediction Done. ID: {aid}")
        
        # 2. Explain
        url_explain = f"http://localhost:8000/api/mrsa/explain/{aid}"
        print(f"Explaining ID {aid}...")
        explain_req = urllib.request.Request(url_explain, headers=headers)
        with urllib.request.urlopen(explain_req, context=ctx) as exp_response:
             explanation = json.loads(exp_response.read().decode())
             print("\nExplanation Features:")
             
             for item in explanation['explanations']:
                 print(f" - {item['feature']} (Impact: {item['impact']}) | Value: {item['value']}")
                 
             for item in explanation['explanations']:
                 print(f" - {item['feature']} (Impact: {item['impact']}) | Value: {item['value']}")
                 
             # Check for incorrect sample types (We selected Blood)
             found_wrong = any(x in item['feature'] for item in explanation['explanations'] for x in ["Urine", "Pus/Wound", "Sputum"])
             if found_wrong:
                 print("\n❌ FAILURE: Unselected Sample Types found!")
             else:
                 print("\n✅ SUCCESS: Unselected Sample Types filtered out.")

except Exception as e:
    print(f"\nError: {e}")
    # Try to read error body if it's an HTTPError
    if hasattr(e, 'read'):
        print(f"Body: {e.read().decode()}")
    sys.exit(1)
