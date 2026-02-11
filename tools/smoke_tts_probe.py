import requests
import sys

API_URL = "http://127.0.0.1:8001/api"

def test_probe():
    print("Smoking TTS Probe...")
    try:
        res = requests.get(f"{API_URL}/tts/device_probe")
        if res.status_code != 200:
            print(f"Probe failed: {res.status_code}")
            sys.exit(1)
            
        data = res.json()
        print(f"Probe Data: {data}")
        
        if "supported" not in data or "reason" not in data:
            print("Invalid schema")
            sys.exit(1)
            
        print("PASS")
    except Exception as e:
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    test_probe()
