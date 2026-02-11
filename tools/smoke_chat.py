import asyncio
import aiohttp
import sys
import subprocess
import time
import os
import json

def get_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

async def check_server_health(port):
    url = f"http://localhost:{port}/api/health"
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < 20:
            try:
                async with session.get(url, timeout=1.0) as resp:
                    if resp.status == 200:
                        return True
            except:
                pass
            print(f"Waiting for server on {port}...", file=sys.stderr)
            await asyncio.sleep(1.0)
    return False

async def smoke_chat(port):
    base_url = f"http://localhost:{port}/api"
    
    # 1. Check OpenAPI presence
    async with aiohttp.ClientSession() as session:
        print("Checking OpenAPI schema...")
        async with session.get(f"http://localhost:{port}/openapi.json") as resp:
            data = await resp.json()
            paths = data.get("paths", {})
            
            # Debug Print
            found_paths = sorted(list(paths.keys()))
            if "/api/llm/chat" not in paths:
                print(f"FAILURE: /api/llm/chat missing. Found: {found_paths}")
                return False
            else:
                print("SUCCESS: /api/llm/chat found in OpenAPI.")

        # 2. Start Run
        async with session.post(f"{base_url}/runs/start") as resp:
            data = await resp.json()
            run_id = data["run_id"]
            print(f"Run started: {run_id}")

        # 3. Send Chat
        print("Sending chat value...")
        payload = {"run_id": run_id, "message": "Test Message"}
        async with session.post(f"{base_url}/llm/chat", json=payload) as resp:
            if resp.status != 200:
                print(f"Chat failed: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return False
            data = await resp.json()
            print(f"Chat OK: {data.get('status', 'ok')}")

        # 4. Verify Artifact
        # Give file system a moment
        await asyncio.sleep(1.0)
        conv_path = f"runs/{run_id}/artifacts/conversation.json"
        
        for _ in range(3):
            if os.path.exists(conv_path):
                with open(conv_path, "r") as f:
                    history = json.load(f)
                    if len(history) >= 2:
                        print("SUCCESS: Conversation history valid.")
                        return True
            await asyncio.sleep(1.0)
            
        print("FAILURE: conversation.json missing or incomplete")
        return False

def main():
    port = get_free_port()
    print(f"Starting server on {port}...")
    
    # Use DEVNULL to avoid PIPE buffer deadlock
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "orca_api.main:app", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if not loop.run_until_complete(check_server_health(port)):
            print("Server failed to start")
            sys.exit(1)
            
        success = loop.run_until_complete(smoke_chat(port))
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    main()
