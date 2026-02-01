import requests
import os

url = "http://localhost:8000/upload"
file_path = "app/test_data/invoice1.png"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, "rb") as f:
    files = {"file": ("invoice1.png", f, "image/png")}
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
