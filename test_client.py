import requests
import sys
import json
import os

API_URL = "http://localhost:8000/upload"

def upload_bill(image_path):
    if not os.path.exists(image_path):
        print(f"Error: File not found at {image_path}")
        return

    print(f"Uploading {image_path} to {API_URL}...")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(API_URL, files=files)
        
        if response.status_code == 200:
            print("\n✅ Success! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\n❌ Error {response.status_code}:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {API_URL}.")
        print("Make sure the FastAPI server is running (uvicorn app.main:app --reload)")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <path_to_image>")
        print("Example: python test_client.py ./sample_invoice.jpg")
    else:
        upload_bill(sys.argv[1])
