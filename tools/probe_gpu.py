import sys
import json
import torch

def probe():
    res = {
        "supported": False,
        "reason": "unknown",
        "device_name": None,
        "cuda_version": None,
        "torch_version": torch.__version__
    }
    
    if not torch.cuda.is_available():
        res["reason"] = "no_cuda"
        print(json.dumps(res))
        return

    try:
        res["cuda_version"] = torch.version.cuda
        res["device_name"] = torch.cuda.get_device_name(0)
        cc = torch.cuda.get_device_capability(0)
        res["sm"] = f"sm_{cc[0]}{cc[1]}"
        
        # Test
        try:
            x = torch.randn(1, device="cuda")
            y = x + 1
            z = y.cpu()
            res["supported"] = True
            res["reason"] = "ok"
        except RuntimeError as e:
            if "no kernel image" in str(e) or "device-side assert" in str(e):
                res["reason"] = "unsupported_sm"
            else:
                res["reason"] = "torch_no_kernels"
                
    except Exception as e:
        res["reason"] = str(e)
        
    print(json.dumps(res))

if __name__ == "__main__":
    probe()
