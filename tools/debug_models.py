import sys
import asyncio

# Add project root to path
sys.path.append(".")

from orca_api.llm_gateway.router import check_ollama

async def main():
    print("Running check_ollama inside app context...")
    res = await check_ollama()
    print(f"Result: {res}")
    
    if res.get("active"):
        print("PASS: Ollama is active.")
    else:
        print("FAIL: Ollama is inactive.")

if __name__ == "__main__":
    asyncio.run(main())
