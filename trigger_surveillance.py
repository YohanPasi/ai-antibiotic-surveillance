import urllib.request
import json
import time

url = "http://localhost:8000/api/predict"
# Validated Combo from DB: Ward 02 / Pseudomonas / Meropenem (MEM) (n=4)
payload = {
    "organism": "Pseudomonas aeruginosa",
    "antibiotic": "Meropenem  (MEM)",
    "ward": "02"
}
data = json.dumps(payload).encode('utf-8')
headers = {"Content-Type": "application/json"}

print(f"Triggering Surveillance Logic at {url}...")

# 3 Requests to simulate persistence history
for i in range(1, 4):
    print(f"\n--- Request {i} ---")
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                resp_body = response.read().decode('utf-8')
                resp_json = json.loads(resp_body)
                print("Status:", resp_json.get("alert_level"))
                print("Message:", resp_json.get("message"))
                print("Model:", resp_json.get("model_used"))
            else:
                print(f"Error {response.status}")
    except Exception as e:
        print(f"Exception: {e}")
    
    time.sleep(1)
