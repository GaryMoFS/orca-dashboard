
import sys
import os
import asyncio
import logging

# Configure path to allow imports
sys.path.append(os.getcwd())

# Mute logger for cleaner output
logging.getLogger("GPUOrchestrator").setLevel(logging.WARNING)

from orca_runtime.gpu_orchestrator import GPUOrchestrator, ModelType, GPUTier

async def run_scenario(name, vram_mb, model_type, model_name):
    print(f"\n--- SCENARIO: {name} ---")
    
    # Instantiate
    orch = GPUOrchestrator()
    
    # FORCE OVERRIDE HARDWARE DETECTION FOR TEST
    orch.total_memory_mb = vram_mb
    orch._determine_tier() # Recalculate tier based on forced VRAM
    
    print(f"Simulated VRAM: {vram_mb} MB -> Tier: {orch.tier.value}")
    
    # Request
    directives = await orch.prepare_for_model(model_type, model_name)
    
    print(f"Directives Received: {directives}")
    print(f"Active Models State: {orch.models_active}")
    
    return directives, orch

async def main():
    print("Initializing GPU Orchestrator Test Suite...")
    
    # 1. Low Tier GPU (8GB) - Request LLM
    try:
        d, _ = await run_scenario("Low Tier (8GB) - Request LLM", 8192, ModelType.LLM, "llama3:8b")
        # Directives keep_alive should be 0 (transient/on-demand)
        if d.get("keep_alive") == 0:
            print("PASS: Low Tier enforces transient loading (keep_alive=0).")
        else:
            print(f"FAIL: Low Tier allowed keep_alive={d.get('keep_alive')}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 2. Mid Tier GPU (16GB) - Request LLM
    try:
        d, _ = await run_scenario("Mid Tier (16GB) - Request LLM", 16384, ModelType.LLM, "llama3:8b")
        # Directives keep_alive should be -1 (persistent)
        if d.get("keep_alive") == -1:
            print("PASS: Mid Tier allows persistent LLM.")
        else:
             print(f"FAIL: Expected keep_alive=-1, got {d.get('keep_alive')}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 3. Mid Tier - Request TTS (Transient)
    try:
        d, _ = await run_scenario("Mid Tier (16GB) - Request TTS", 16384, ModelType.TTS, "tara")
        # Directives keep_alive should be 0 (transient) for TTS in MID tier
        if d.get("keep_alive") == 0:
            print("PASS: Mid Tier enforces transient TTS.")
        else:
             print(f"FAIL: Expected keep_alive=0 for TTS in Mid Tier, got {d.get('keep_alive')}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 4. High Tier GPU (24GB) - Request Everything
    try:
        d, _ = await run_scenario("High Tier (24GB) - Request TTS", 24576, ModelType.TTS, "orpheus_voice")
        if d.get("keep_alive") == -1:
            print("PASS: High Tier allows persistent TTS.")
        else:
             print(f"FAIL: Expected keep_alive=-1, got {d.get('keep_alive')}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 5. Telemetry Check
    orch = GPUOrchestrator()
    status = orch.get_status()
    print(f"\nTelemetry Output Stub:\n{status}")

if __name__ == "__main__":
    asyncio.run(main())
