import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:7010"
TIMEOUT = 5.0

def log(msg, color="white"):
    print(msg)

def check_endpoint(url):
    start = time.time()
    try:
        r = httpx.get(url, timeout=TIMEOUT)
        dur = (time.time() - start) * 1000
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text, dur
    except Exception as e:
        dur = (time.time() - start) * 1000
        return False, str(e), dur

def main():
    log("=== ORCA Runtime Smoke Test ===")
    
    # 1. Check Status
    # 1. Check Status
    log(f"1. Checking Status ({BASE_URL}/runtime/status)...")
    ok, data, dur = check_endpoint(f"{BASE_URL}/runtime/status")
    if not ok:
        log(f"FAIL: /runtime/status -> {data} ({dur:.0f}ms)", "red")
        return
    log(f"OK: Status returned in {dur:.0f}ms", "green")

    # 2. List Providers
    log("\n2. Listing Providers...")
    # 2. List Providers
    log("\n2. Listing Providers...")
    ok, data, dur = check_endpoint(f"{BASE_URL}/runtime/providers")
    if not ok:
        log(f"FAIL: {data} ({dur:.0f}ms)", "red")
        return
    log(f"Found {len(data)} providers:", "green")
    for p in data:
        log(f" - {p['id']} ({p['label']}) -> {p['capabilities']}")

    # 3. Check Models for each
    log("\n3. Checking Models...")
    for p in data:
        pid = p['id']
    for p in data:
        pid = p['id']
        ok, mdata, dur = check_endpoint(f"{BASE_URL}/runtime/providers/{pid}/models")
        if ok:
            models = mdata.get('models', [])
            log(f" - {pid}: {len(models)} models found ({models[:3]}...)", "green")
        else:
            log(f" - {pid}: Failed to list models", "red")

    # 4. Device Advisor
    log("\n4. Checking Device Advisor...")
    model = "llama3:8b"
    prov = "ollama"
    model = "llama3:8b"
    prov = "ollama"
    ok, adv, dur = check_endpoint(f"{BASE_URL}/runtime/device/advise?model={model}&provider={prov}")
    if ok:
        log(f"Advice for {model} on {prov}: {adv}", "green")
    else:
        log("FAIL Advisor", "red")

if __name__ == "__main__":
    main()
