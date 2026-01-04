import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "http://localhost:8000/api/master/definitions/WARD"

try:
    print(f"GET {url}...")
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        print(json.dumps(data, indent=2))
        if len(data) >= 5:
             print("✅ API Verification Passed")
        else:
             print("❌ API Verification Failed")
except Exception as e:
    print(f"Error: {e}")
