import requests

url = "http://localhost:8000/api/beta-lactam/evaluate"
payload = {
    "inputs": {
        "patient_id": "PT-TEST",
        "Age": "65",
        "Gender": "Male",
        "Ward": "ICU",
        "Organism": "E_coli",
        "Gram": "GNB",
        "Sample_Type": "Blood",
        "Cell_Count_Level": "High"
    },
    "ast_available": False
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)
