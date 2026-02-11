import torch
import sys
import os

def test():
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    print(f"CUDA Version (Torch): {torch.version.cuda}")
    
    if not torch.cuda.is_available():
        print("FAIL: CUDA not available in PyTorch.")
        return

    print(f"Device Count: {torch.cuda.device_count()}")
    dev = torch.cuda.get_device_name(0)
    print(f"Device 0: {dev}")
    
    # helper for memory
    def mem_info():
        free, total = torch.cuda.mem_get_info(0)
        print(f"Memory: {free/1024**3:.2f} GB Free / {total/1024**3:.2f} GB Total")
        return free

    free_mem = mem_info()
    
    if free_mem < 1 * 1024**3: # Less than 1GB free
        print("WARNING: Extremely low VRAM. Allocations will likely fail.")
    
    try:
        print("Attempting Tiny Allocation (1MB)...")
        x = torch.ones(256, 1024, device="cuda")
        print("Success: Allocation 1.")
        print("Attempting Computation (x * 2)...")
        y = x * 2
        print("Success: Computation.")
        print("Result mean:", y.mean().item())
        
        # Test Blackwell specific (BF16 check?)
        print("Attempting BF16 Allocation...")
        z = torch.ones(10, 10,  dtype=torch.bfloat16, device="cuda")
        print("Success: BF16 Allocation.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
