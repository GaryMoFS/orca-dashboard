import requests
import json
import time

API_URL = "http://127.0.0.1:1234/v1/completions"
HEADERS = {"Content-Type": "application/json"}
PROMPT = "<|audio|>tara: Test.<|eot_id|>"
PAYLOAD = {
    "model": "orpheus-3b-0.1-ft-q4_k_m",
    "prompt": PROMPT,
    "max_tokens": 100, # Small for test
    "temperature": 0.6,
    "stream": True
}

print(f"Calling {API_URL}...")
start = time.time()
try:
    with requests.post(API_URL, headers=HEADERS, json=PAYLOAD, stream=True, timeout=10) as r:
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            for line in r.iter_lines():
                if line:
                    print(f"Line: {line.decode('utf-8')[:100]}...") # Truncate
                    break # Just prove it streams
        else:
            print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")

print(f"Time: {time.time() - start:.2f}s")
