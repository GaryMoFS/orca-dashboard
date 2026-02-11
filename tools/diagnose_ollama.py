import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/tags"

print("Checking Ollama Service...")
try:
    start = time.time()
    res = requests.get(OLLAMA_URL, timeout=5)
    latency = (time.time() - start) * 1000
    
    if res.status_code == 200:
        data = res.json()
        models = [m['name'] for m in data.get('models', [])]
        print(f"[OK] Ollama is UP ({latency:.1f}ms)")
        print(f"     Models: {models}")
        
        # Test Generate (Tiny Test)
        if models:
            test_model = models[0]
            print(f"Testing generation with {test_model}...")
            gen_url = "http://localhost:11434/api/generate"
            payload = {
                "model": test_model,
                "prompt": "Hello",
                "stream": False
            }
            res_gen = requests.post(gen_url, json=payload, timeout=10)
            if res_gen.status_code == 200:
                print(f"[OK] Generation Success: {res_gen.json().get('response', '')[:20]}...")
            else:
                print(f"[FAIL] Generation Error: {res_gen.status_code}")
                print(f"       {res_gen.text}")
        else:
            print("[WARN] No models found. Pull a model using 'ollama pull llama3'")
            
    else:
        print(f"[FAIL] Ollama API Error: {res.status_code}")
        
except Exception as e:
    print(f"[FAIL] Connection Error: {e}")
    print("Ensure Ollama is running (check task manager or run 'ollama serve')")
