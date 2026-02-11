import requests
import os

def test_tts():
    url = "http://127.0.0.1:7010/runtime/tts"
    payload = {
        "text": "Hello.",
        "voice": "tara"
    }
    
    # Ensure artifacts directory exists
    os.makedirs("artifacts/_smoke", exist_ok=True)
    output_path = "artifacts/_smoke/tts_test.wav"
    
    print(f"Testing TTS: Posting to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=180)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response size: {len(response.content)} bytes")
        
        # Assertions
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "audio/wav" in response.headers.get("Content-Type", ""), "Expected audio/wav content type"
        
        # Check if response is 'null' (4 bytes)
        if response.content == b"null":
             print("FAILURE: Received 'null' response!")
             raise AssertionError("Received 'null' response instead of WAV bytes.")
        
        assert len(response.content) > 1000, f"Response too small: {len(response.content)} bytes"
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"SUCCESS: Saved {len(response.content)} bytes to {output_path}")
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
        if 'response' in locals() and response is not None:
            print("First 100 bytes of response:")
            print(response.content[:100])
        exit(1)

if __name__ == "__main__":
    test_tts()
