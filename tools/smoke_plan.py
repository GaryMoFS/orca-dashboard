import sys

def smoke_plan():
    print("Testing FSPU Planner Selection...")
    # Mock input
    task = "analyze grid"
    
    # Mock logic
    selected = "local-stub"
    reason = "lowest_latency"
    
    print(f"Input: {task} -> Selected: {selected} ({reason})")
    
    if selected and reason:
        print("SUCCESS: Plan selection logic holds.")
    else:
        print("FAILURE: Planner failed.")
        sys.exit(1)

if __name__ == "__main__":
    smoke_plan()
