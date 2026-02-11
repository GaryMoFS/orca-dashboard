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

async def smoke_system(port):
    url = f"http://localhost:{port}/api/system/now"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"FAILURE: status {resp.status}")
                    return False
                
                data = await resp.json()
                print(f"System Time: {data}")
                
                # Check required fields
                required = ["iso", "tz", "weekday", "epoch_ms"]
                missing = [k for k in required if k not in data]
                
                if missing:
                    print(f"FAILURE: Missing keys {missing}")
                    return False
                
                return True
    except Exception as e:
        print(f"FAILURE: Exception {e}")
        return False

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
            
        success = loop.run_until_complete(smoke_system(port))
        
        if success:
            print("SUCCESS: System check passed")
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
