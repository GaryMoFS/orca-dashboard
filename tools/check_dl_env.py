import sys

def check_package(name):
    try:
        pkg = __import__(name)
        print(f"OK: {name} installed (ver: {getattr(pkg, '__version__', 'unknown')})")
        return pkg
    except ImportError:
        print(f"MISSING: {name}")
        return None

print("Checking Deep Learning Environment...")
torch = check_package("torch")
transformers = check_package("transformers")
scipy = check_package("scipy")

if torch:
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        
if torch and transformers and scipy:
    print("\nSUCCESS: You have the necessary libraries to run Hugging Face TTS models locally!")
else:
    print("\nWARNING: Some libraries are missing. You may need to pip install them.")
