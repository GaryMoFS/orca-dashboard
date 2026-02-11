import asyncio
import aiohttp
import sys
import subprocess
import time
import os
import hashlib

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

async def smoke_upload(port):
    url = f"http://localhost:{port}/api/files/upload"
    
    # Create test content
    content = b"Hello ORCA Upload Test"
    expected_sha = hashlib.sha256(content).hexdigest()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Use multipart
            data = aiohttp.FormData()
            data.add_field("file", content, filename="test_upload.txt", content_type="text/plain")
            # Run ID omitted -> general upload
            
            async with session.post(url, data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"FAILURE: status {resp.status} - {text}")
                    return False
                
                res_data = await resp.json()
                print(f"Upload Result: {res_data}")
                
                # Check response fields
                if res_data["sha256"] != expected_sha:
                     print(f"FAILURE: Hash mismatch. Got {res_data['sha256']}, expected {expected_sha}")
                     return False
                
                path = res_data["path"]
                # Verify file exists
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        saved = f.read()
                        if saved == content:
                            print("SUCCESS: File saved correctly")
                            # Clean up
                            try:
                                os.remove(path)
                                # Try to remove dir if empty (runs/_uploads/<epoch>)
                                os.rmdir(os.path.dirname(path))
                            except:
                                pass
                            return True
                        else:
                            print("FAILURE: Saved content mismatch")
                            return False
                else:
                    print(f"FAILURE: File not found at {path}")
                    return False
                    
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
            
        success = loop.run_until_complete(smoke_upload(port))
        
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
