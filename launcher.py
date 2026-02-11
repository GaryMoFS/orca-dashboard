import os
import json
import subprocess
import time
import socket
import webbrowser
import sys
import shutil
import urllib.request
import urllib.error

# Configuration File
CONFIG_FILE = "orca_config.json"

# Defaults
DEFAULT_CONFIG = {
    "llm_provider": "ollama", 
    "tts_provider": "lm_studio",
    "chat_mode": "offline",
    "tts_mode": "offline"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                merged = {**DEFAULT_CONFIG, **json.load(f)}
                # Backward compatibility: old config used "orpheus" as tts_provider.
                if merged.get("tts_provider") == "orpheus":
                    fallback = merged.get("llm_provider", "lm_studio")
                    merged["tts_provider"] = fallback if fallback in {"ollama", "lm_studio"} else "lm_studio"
                return merged
        except:
            pass
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def wait_for_service(url, name, timeout=15):
    print(f"Waiting for {name} ({url})...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    print(f"[{name}] Ready!")
                    return True
        except:
            time.sleep(1)
            print(".", end="", flush=True)
    print(f"\n[WARN] {name} timed out. Proceeding anyway.")
    return False

def start_visible_process(command, title, cwd=None):
    print(f"[{title}] Starting in new window...")
    # Construct a command that opens a new window and keeps it open on error/exit (/k)
    # We use 'start' which is a Windows shell command.
    
    # Escape quotes in the command if necessary, but keep it simple
    if cwd:
        # Change directory first in the new cmd
        full_cmd = f'start "{title}" cmd /k "cd /d {cwd} && {command}"'
    else:
        full_cmd = f'start "{title}" cmd /k "{command}"'
        
    os.system(full_cmd)

def main():
    print("===================================================")
    print("  ORCA DASHBOARD LAUNCHER")
    print("===================================================")
    
    config = load_config()
    save_config(config)

    # 1. Start LLM Providers
    # A) LM Studio (Required for local Orpheus TTS OR if selected as Chat/TTS model host)
    start_lm = False
    if config.get("tts_mode", "offline") != "cloud": start_lm = True
    if config.get("llm_provider") == "lm_studio": start_lm = True
    if config.get("tts_provider") == "lm_studio": start_lm = True
    
    if start_lm:
        if not is_port_open(1234):
            # Check if lms is in path - warn if not, but try anyway so user sees error in window
            if not shutil.which("lms"):
                print("[WARN] 'lms' not found in PATH. Window may show error.")
            start_visible_process("lms server start --port 1234 --bind 127.0.0.1", "LM Studio")
        else:
            print("[LM Studio] Already running on port 1234")

    # B) Ollama (Required if selected as Chat)
    start_ollama = False
    if config.get("llm_provider") == "ollama": start_ollama = True
    
    if start_ollama:
        if not is_port_open(11434):
            if not shutil.which("ollama"):
                 print("[WARN] 'ollama' not found in PATH. Window may show error.")
            start_visible_process("ollama serve", "Ollama")
        else:
            print("[Ollama] Already running on port 11434")

    # 2. Start TTS Provider Engine (Orpheus service)
    tts_mode = config.get("tts_mode", "offline")
    if tts_mode != "cloud":
        if not is_port_open(5005):
            orpheus_path = r"C:\Users\Gary\Orpheus-FastAPI-LMStudio"
            if os.path.exists(orpheus_path):
                # Using cmd /K to keep window open
                cmd = f'venv\\Scripts\\activate && python app.py'
                start_visible_process(cmd, "Orpheus TTS", cwd=orpheus_path)
            else:
                print(f"[Orpheus TTS] Path not found: {orpheus_path}")
        else:
             print("[Orpheus TTS] Already running on port 5005")

    # 3. Start ORCA Runtime
    if not is_port_open(7010):
        # Run as module from current directory
        cmd = f'python -m orca_runtime.main'
        start_visible_process(cmd, "ORCA Runtime", cwd=os.getcwd())
    else:
        print("[ORCA Runtime] Already running on port 7010")

    # 4. Start Backend (API)
    if not is_port_open(8001):
        cmd = f'python -m uvicorn orca_api.main:app --host 127.0.0.1 --port 8001 --reload'
        start_visible_process(cmd, "ORCA Backend", cwd=os.getcwd())
    else:
        print("[ORCA Backend] Already running on port 8001")
        
    # Wait for backend
    wait_for_service("http://127.0.0.1:8001/docs", "ORCA Backend")
    wait_for_service("http://127.0.0.1:7010/docs", "ORCA Runtime")

    # 5. Start Frontend
    if not is_port_open(5173):
        frontend_dir = os.path.join(os.getcwd(), "orca_dashboard", "web")
        # Bind to IPv4 explicitly to fix "Unreachable" errors on Windows
        cmd = f'python -m http.server 5173 --bind 127.0.0.1'
        start_visible_process(cmd, "ORCA Frontend", cwd=frontend_dir)
        # Wait for frontend to actually serve
        wait_for_service("http://127.0.0.1:5173", "Frontend UI")
    else:
        print("[ORCA Frontend] Already running on port 5173")

    # 6. Launch Browser
    print("Opening Dashboard...")
    # Cache Busting
    webbrowser.open(f"http://localhost:5173/?v={int(time.time())}")
    
    print("\nServices are launching in separate windows...")
    print("IMPORTANT: If dropdowns are missing, please refresh your browser (Ctrl+F5).")
    print("You can close this launcher window (services will keep running).")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
