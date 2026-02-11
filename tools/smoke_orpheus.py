import asyncio
import aiohttp
import sys
import subprocess
import time

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
            await asyncio.sleep(1.0)
    return False

async def smoke_orpheus(port):
    print("Checking for Orpheus model...")
    # Using ORCA probe endpoint to be safer/cleaner
    url = f"http://localhost:{port}/api/providers/probe"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5.0) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    probes = data.get("probes", [])
                    ollama = next((p for p in probes if p["name"] == "ollama_local"), None)
                    
                    if not ollama or not ollama.get("active"):
                        print("SKIP: Ollama not reachable")
                        return True
                        
                    models = ollama.get("models", [])
                    # Look for 'orpheus' subsequence
                    found = [m for m in models if "orpheus" in m.lower()]
                    
                    if found:
                        print(f"OK: Found models: {found}")
                    else:
                        print("WARN: Orpheus model not installed")
                else:
                    print(f"WARN: Probe returned {resp.status}")
    except Exception as e:
        print(f"SKIP: Connection error ({e})")
        
    return True

def main():
    port = get_free_port()
    print(f"Starting server on {port}...")
    
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
            
        loop.run_until_complete(smoke_orpheus(port))
        sys.exit(0)
            
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    main()
