import asyncio
import aiohttp
import sys
import subprocess
import time
import os
import json
import signal

# Reuse logic from smoke_events.py ideally, but simplified here for isolation
def get_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

async def check_server_health(port):
    url = f"http://localhost:{port}/api/health"
    async with aiohttp.ClientSession() as session:
        for _ in range(20):
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return True
            except:
                pass
            await asyncio.sleep(0.5)
    return False

async def smoke_llm(port):
    base_url = f"http://localhost:{port}/api"
    
    # 1. Start Run
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/runs/start") as resp:
            data = await resp.json()
            run_id = data["run_id"]
            print(f"Run started: {run_id}")

        # 2. Call LLM Generate
        print("Calling LLM Generate...")
        payload = {
            "run_id": run_id,
            "prompt": "Say OK",
            "stream": False
        }
        async with session.post(f"{base_url}/llm/generate", json=payload) as resp:
            if resp.status != 200:
                print(f"FAILURE: Generate failed {resp.status}")
                return False
            
            gen_data = await resp.json()
            print(f"Gen Response: {gen_data}")
            
            if "status" not in gen_data or gen_data["status"] != "completed":
                print("FAILURE: Status not completed")
                return False

        # 3. Check Artifact
        artifact_path = f"runs/{run_id}/artifacts/llm_output.txt"
        meta_path = f"runs/{run_id}/artifacts/llm_output.meta.json"
        
        if os.path.exists(artifact_path):
            with open(artifact_path, "r") as f:
                content = f.read()
                print(f"Artifact Content: {content[:50]}...")
                if len(content) > 0:
                    print("SUCCESS: Artifact created and seeded.")
                else: 
                     print("FAILURE: Artifact empty")
                     return False
        else:
            print("FAILURE: Artifact missing.")
            return False

        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
                if "output_sha256" in meta and "prompt_sha256" in meta:
                    print("SUCCESS: Metadata file valid.")
                else:
                    print("FAILURE: Metadata missing keys")
                    return False
        else:
            print("FAILURE: Metadata file missing.")
            return False
            
        return True
            
    return False

def main():
    port = get_free_port()
    print(f"Starting server on {port}...")
    
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "orca_api.main:app", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Run test loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if not loop.run_until_complete(check_server_health(port)):
            print("Server failed to start")
            sys.exit(1)
            
        success = loop.run_until_complete(smoke_llm(port))
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
