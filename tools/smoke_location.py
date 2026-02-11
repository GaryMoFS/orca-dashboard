import requests
import time
import sys
import os
import shutil

API_URL = "http://127.0.0.1:8001/api"

def test_location():
    print("Smoking Location Endpoint...")
    
    # payload
    payload = {
        "lat": -33.86,
        "lon": 151.20,
        "accuracy_m": 50.0,
        "source": "smoke_test"
    }
    
    try:
        # POST
        res = requests.post(f"{API_URL}/system/location", json=payload)
        if res.status_code != 200:
            print(f"POST failed: {res.status_code} {res.text}")
            sys.exit(1)
            
        print("POST /system/location OK")
        
        # GET
        res = requests.get(f"{API_URL}/system/location")
        if res.status_code != 200:
            print(f"GET failed: {res.status_code}")
            sys.exit(1)
            
        data = res.json()
        print(f"GET data: {data}")
        
        if data.get("lat") != -33.86:
            print("Mismatch in stored data")
            sys.exit(1)
            
        # Verify File
        loc_file = "runs/_system/location.json"
        if not os.path.exists(loc_file):
             print(f"Artifact file missing: {loc_file}")
             sys.exit(1)
             
        print("Artifact file verified.")
        print("PASS")

    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_location()
