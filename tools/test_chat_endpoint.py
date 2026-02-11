import requests
import json
import uuid

def test_chat():
    # 1. Start Run correctly
    resp = requests.post("http://127.0.0.1:8001/api/runs/start")
    if resp.status_code != 200:
        print(f"Start Run Failed: {resp.status_code}")
        return
    
    run_id = resp.json()["run_id"]
    print(f"Run Started: {run_id}")

    url = "http://127.0.0.1:8001/api/llm/chat"
    payload = {
        "run_id": run_id,
        "message": "Start run",
        "model": "llama3:latest",
        "temperature": 0.7
    }
    
    print(f"Testing POST {url}...")
    try:
        resp = requests.post(url, json=payload, timeout=60)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
