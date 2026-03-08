import requests, json

try:
    url = 'http://127.0.0.1:8000/api/analysis/target?ward=01&organism=Pseudomonas%20aeruginosa&antibiotic=Amikacin%20(AK)'
    res = requests.get(url)
    data = res.json()
    print('DRIFT ANALYSIS KEYS:', list(data.get('drift_analysis', {}).keys()))
    print('Bypass reason included?', 'bypass_reason' in data.get('drift_analysis', {}))
    print('STATUS CODE:', res.status_code)
except Exception as e:
    print('ERROR:', e)
