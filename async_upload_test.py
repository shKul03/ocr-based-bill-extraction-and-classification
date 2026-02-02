import requests
import time
import json
import sys

UPLOAD_URL = "http://localhost:8000/upload"
ALL_URL = "http://localhost:8000/all"
FILE_PATH = "app/test_data/invoice1.png"

def test_async_upload():
    print(f"--- Testing Async Upload ---")
    
    # 1. Upload Document
    start_time = time.time()
    try:
        with open(FILE_PATH, "rb") as f:
            files = {"file": ("invoice1.png", f, "image/png")}
            response = requests.post(UPLOAD_URL, files=files)
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    duration = time.time() - start_time
    print(f"Upload took {duration:.2f} seconds")

    if response.status_code != 200:
        print(f"Upload failed with status {response.status_code}: {response.text}")
        return

    data = response.json()
    print("Immediate Response:")
    print(json.dumps(data, indent=2))

    # Validate Immediate Response
    if data.get("status") != "classified":
        print("FAIL: Status is not 'classified'")
        return
    if "bill_type" not in data or "bill_subtype" not in data:
        print("FAIL: Missing classification info")
        return
    
    doc_id = data.get("document_id")
    print(f"Document ID: {doc_id}")

    # 2. Poll for Background Completion
    print("Polling /all for document completion...")
    found = False
    for i in range(20): # Try for 20 * 5 = 100 seconds (long poll due to LLM)
        time.sleep(5)
        try:
            r = requests.get(ALL_URL)
            if r.status_code == 200:
                all_docs = r.json()
                # Check if our doc is there and has extracted data
                target_doc = next((d for d in all_docs if d["document_id"] == doc_id), None)
                if target_doc:
                    print(f"Found document in /all after {(i+1)*5} seconds")
                    print(json.dumps(target_doc, indent=2))
                    found = True
                    break
        except Exception:
            pass
    
    if not found:
        print("Timed out waiting for background processing to complete.")
    else:
        print("SUCCESS: Background processing verified.")

if __name__ == "__main__":
    test_async_upload()
