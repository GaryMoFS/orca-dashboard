import asyncio
import websockets
import requests
import json
import sys
import subprocess
import time
import socket
import os
import signal

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def wait_for_server(url, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                print("Server is ready.")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    return False

async def run_test(port):
    base_url = f"http://localhost:{port}/api"
    ws_url = f"ws://localhost:{port}/api/ws/events"
    
    # 1. Start Run
    print(f"POST {base_url}/runs/start")
    resp = requests.post(f"{base_url}/runs/start")
    if resp.status_code != 200:
        print(f"Failed to start run: {resp.text}")
        return False
    
    run_data = resp.json()
    run_id = run_data["run_id"]
    print(f"Run started: {run_id}")
    
    # 2. Connect WS and Listen
    print(f"Connecting to {ws_url}")
    try:
        async with websockets.connect(ws_url) as websocket:
            print("WS Connected. Sending handshake...")
            await websocket.send("Hello Smoke Test")
            
            # 3. Trigger Close to generate event
            print(f"POST {base_url}/runs/{run_id}/close")
            requests.post(f"{base_url}/runs/{run_id}/close")
            
            # 4. Read messages
            received_closed = False
            try:
                # We expect a few messages: run_started (broadcasted on start), run_closed
                # Since we connected AFTER start, we might verify receiving 'Server received' echo or run_closed
                # Let's wait for run_closed
                for _ in range(3):
                    msg = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    print(f"WS RX: {msg}")
                    data = json.loads(msg) if "{" in msg else {}
                    if data.get("type") == "run_closed" and data.get("run_id") == run_id:
                        received_closed = True
                        break
            except asyncio.TimeoutError:
                print("WS Timeout waiting for run_closed event.")

            if not received_closed:
                print("FAILURE: Did not receive run_closed event via WS")
                return False
                
    except Exception as e:
        print(f"WS Error: {e}")
        return False

    # 5. Verify Artifacts
    if os.path.exists(f"runs/{run_id}_events.jsonl"):
        print(f"SUCCESS: Artifact runs/{run_id}_events.jsonl found.")
    else:
        print(f"FAILURE: Artifact runs/{run_id}_events.jsonl MISSING.")
        return False
        
    return True

def main():
    port = get_free_port()
    print(f"Starting uvicorn on port {port}...")
    
    # Start Server
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "orca_api.main:app", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        if not wait_for_server(f"http://localhost:{port}/api/health"):
            print("Server failed to start.")
            sys.exit(1)
            
        # Run Async Test
        success = asyncio.run(run_test(port))
        
        if success:
            print("Smoke Check: PASSED")
            sys.exit(0)
        else:
            print("Smoke Check: FAILED")
            sys.exit(1)
            
    finally:
        print("Killing server...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
