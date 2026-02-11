import requests
import json
import os
import datetime

ORPHEUS_BASE = "http://127.0.0.1:5005"
TIMESTAMP = "260210_0847"
ARTIFACTS_DIR = f"_verification_artifacts/{TIMESTAMP}"

def probe():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    print(f"Probing {ORPHEUS_BASE}...")
    
    # 1. Health
    try:
        r = requests.get(f"{ORPHEUS_BASE}/health", timeout=5)
        print(f"Health: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Health Check Failed: {e}")

    # 2. OpenAPI
    try:
        r = requests.get(f"{ORPHEUS_BASE}/openapi.json", timeout=5)
        print(f"OpenAPI: {r.status_code}")
        if r.status_code == 200:
            paths = r.json().get("paths", {}).keys()
            # Save raw structure too
            with open(f"{ARTIFACTS_DIR}/openapi.json", "w") as f:
                json.dump(r.json(), f, indent=2)
            with open(f"{ARTIFACTS_DIR}/orpheus_paths.txt", "w") as f:
                f.write("\n".join(paths))
            print(f"Saved paths to {ARTIFACTS_DIR}/orpheus_paths.txt")
            print("Paths found:", list(paths))
    except Exception as e:
        print(f"OpenAPI Check Failed: {e}")

    # 3. Test TTS Direct /v1/audio/speech
    payload = {
        "input": "Testing direct connection via v1.",
        "voice": "tara",
        "response_format": "wav"
    }
    try:
        url = f"{ORPHEUS_BASE}/v1/audio/speech"
        print(f"POST {url}...")
        r = requests.post(url, json=payload, timeout=120)
        print(f"TTS v1 Status: {r.status_code}")
        if r.status_code == 200:
            with open(f"{ARTIFACTS_DIR}/tts_via_orpheus_v1.wav", "wb") as f:
                f.write(r.content)
            print(f"Saved {len(r.content)} bytes to tts_via_orpheus_v1.wav")
        else:
            print(f"TTS v1 Failed: {r.text}")
    except Exception as e:
        print(f"TTS v1 Direct Failed: {e}")

    # 4. Test TTS Direct /speak
    payload_speak = {
        "text": "Testing direct connection via speak.",
        "voice": "tara"
    }
    try:
        url = f"{ORPHEUS_BASE}/speak"
        print(f"POST {url}...")
        r = requests.post(url, json=payload_speak, timeout=120)
        print(f"TTS speak Status: {r.status_code}")
        if r.status_code == 200:
             print(f"TTS speak Response: {r.text}")
        else:
            print(f"TTS speak Failed: {r.text}")
    except Exception as e:
        print(f"TTS speak Direct Failed: {e}")

if __name__ == "__main__":
    probe()
