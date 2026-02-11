import requests
import json
import time

def test_gen():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3:latest",
        "prompt": "Say hello",
        "stream": False
    }
    print(f"Sending request to {url}...")
    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=60)
        dur = time.time() - start
        print(f"Status: {resp.status_code}")
        print(f"Duration: {dur:.2f}s")
        if resp.status_code == 200:
            print("Response:", resp.json().get("response"))
        else:
            print("Error:", resp.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_gen()
