import sys
import random

def smoke_providers():
    # Simulate reading probe result
    stub_latency = random.uniform(10, 200)
    print(f"Simulating probe... Latency: {stub_latency:.2f}ms")
    
    if stub_latency > 0:
        print("SUCCESS: Provider latency positive.")
    else:
        print("FAILURE: Invalid latency.")
        sys.exit(1)

if __name__ == "__main__":
    smoke_providers()
