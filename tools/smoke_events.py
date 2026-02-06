import asyncio
import websockets
import json
import uuid
import sys

async def smoke_test():
    uri = "ws://localhost:8000/api/ws/events"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected.")
            await websocket.send("Hello ORCA")
            response = await websocket.recv()
            print(f"< {response}")
            
            if "Server received" in response:
                print("SUCCESS: Websocket echo worked.")
            else:
                print("FAILURE: Unexpected response.")
                sys.exit(1)
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Ensure 'uvicorn orca_api.main:app' is running.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(smoke_test())
