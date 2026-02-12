import subprocess
import time
import httpx
import pytest
import os
import signal
import socket
from contextlib import closing

def get_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

# Dynamic ports
API_PORT = get_free_port()
RUNTIME_PORT = get_free_port()
API_URL = f"http://127.0.0.1:{API_PORT}"
RUNTIME_URL = f"http://127.0.0.1:{RUNTIME_PORT}"

def wait_for_ready(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = httpx.get(url)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def terminate_process(proc):
    if proc is None:
        return
    
    # Try generic termination first
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # Cross-platform process group kill logic
        if os.name == 'nt':
            # Windows
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)])
        else:
            # Unix
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
            except Exception:
                proc.kill()

@pytest.fixture(scope="module")
def start_services():
    """Start orca_api and orca_runtime services with dynamic ports and new sessions."""
    os.makedirs("runs", exist_ok=True)
    
    # Platform-specific process group creation
    popen_kwargs = {}
    if os.name == 'nt':
        # On Windows, use CREATE_NEW_PROCESS_GROUP
        popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        # On Unix, use start_new_session
        popen_kwargs['start_new_session'] = True

    # Start API
    api_proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "orca_api.main:app", "--host", "127.0.0.1", "--port", str(API_PORT)],
        **popen_kwargs
    )
    
    # Start Runtime
    runtime_proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "orca_runtime.main:app", "--host", "127.0.0.1", "--port", str(RUNTIME_PORT)],
        **popen_kwargs
    )
    
    yield (api_proc, runtime_proc)
    
    # Robust cleanup
    terminate_process(api_proc)
    terminate_process(runtime_proc)

def test_api_health(start_services):
    """Verify that orca_api is healthy."""
    assert wait_for_ready(f"{API_URL}/docs"), f"API failed to start on port {API_PORT}"
    response = httpx.get(f"{API_URL}/api/health")
    assert response.status_code == 200
    assert "ok" in response.json()
    assert response.json()["ok"] is True

def test_runtime_health(start_services):
    """Verify that orca_runtime is healthy."""
    assert wait_for_ready(f"{RUNTIME_URL}/docs"), f"Runtime failed to start on port {RUNTIME_PORT}"
    response = httpx.get(f"{RUNTIME_URL}/runtime/status")
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert data["ok"] is True
