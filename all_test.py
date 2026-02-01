import requests
import json

url = "http://localhost:8000/all"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Items found: {len(data)}")
        if len(data) > 0:
            print("First item sample:")
            print(json.dumps(data[0], indent=2))
    else:
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Request failed: {e}")
