import urllib.request
import urllib.error
import json

url = 'http://localhost:8000/api/beta-lactam/evaluate'
data = {
    "inputs": {
        "Age": "65",
        "Gender": "Male",
        "Ward": "02",
        "Sample_Type": "Urine",
        "Organism": "E_coli",
        "Gram": "GNB"
    },
    "ast_available": False
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:")
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"FAILED (HTTP {e.code}):")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"FAILED: {e}")
