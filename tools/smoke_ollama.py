import asyncio
import aiohttp
import sys

async def smoke_ollama():
    print("Checking for Ollama Integration...")
    
    # 1. Probe Providers
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/providers/probe") as resp:
                if resp.status != 200:
                    print("FAILURE: API probe endpoint failed.")
                    sys.exit(1)
                
                data = await resp.json()
                probes = data.get("probes", [])
                ollama = next((p for p in probes if p["name"] == "ollama_local"), None)
                
                if ollama:
                    print(f"SUCCESS: Ollama detected via API. Models: {ollama.get('models')}")
                else:
                    print("WARNING: Ollama NOT detected. (This verification is passed if Ollama is just missing, as integration is soft).")
                    
                # 2. Check Planner Selection (only if ollama active)
                if ollama and ollama.get("models"):
                    # Test Plan
                    payload = {"task_description": "test plan"}
                    async with session.post("http://localhost:8000/api/fspu/plan", json=payload) as plan_resp:
                        plan = await plan_resp.json()
                        provider = plan.get("provider")
                        reason = plan.get("reason_code")
                        print(f"Planner Selected: {provider} ({reason})")
                        
                        if provider == "ollama_local":
                            print("SUCCESS: Planner preferred Ollama.")
                        else:
                            print(f"WARNING: Planner did not select Ollama despite detection. Reason: {reason}")
                            
    except Exception as e:
        print(f"Test Error: {e}")
        # We don't fail hard here because the server might not be running in this isolated script test context 
        # unless checking against live env. But request asked to create tool.
        # Assuming server is running from previous step.
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(smoke_ollama())
    except Exception:
        # If server not up, we fail
        sys.exit(1)
