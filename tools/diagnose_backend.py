import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8001/api"

endpoints = [
    ("GET", "/system/now", "System Time"),
    ("GET", "/providers/probe", "Providers Probe"),
    ("GET", "/tts/voices", "TTS Voices"),
    ("GET", "/llm/models", "LLM Models"),
    ("GET", "/system/location", "Location"),
    ("GET", "/tts/device_probe", "TTS Device Probe")
]

print("--- BACKEND DIAGNOSTIC ---")
failed = False

for method, path, name in endpoints:
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            res = requests.get(url, timeout=3)
        
        if res.status_code == 200:
            print(f"[OK] {name}")
            # print(f"    Payload: {str(res.json())[:100]}...")
        else:
            print(f"[FAIL] {name} - Status: {res.status_code}")
            print(f"       Resp: {res.text}")
            failed = True
            
    except Exception as e:
        print(f"[ERR] {name} - Connection Failed: {e}")
        failed = True

if failed:
    print("\nCONCLUSION: Backend is BROKEN. Check uvicorn logs.")
    sys.exit(1)
else:
    print("\nCONCLUSION: Backend is HEALTHY. Issue is likely Frontend (HTML/JS).")
    sys.exit(0)
