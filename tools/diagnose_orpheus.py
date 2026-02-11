import os
import torch
import sys
import traceback
from transformers import pipeline, SpeechT5HifiGan

MODEL_PATH = r"C:\Users\Gary\models\canopyai\Orpheus-TTS"

print(f"--- ORPHEUS DIAGNOSTIC TOOL ---")
print(f"Checking path: {MODEL_PATH}")

if not os.path.exists(MODEL_PATH):
    print(f"FATAL: Directory does not exist!")
    sys.exit(1)

# List files
print(f"Files found in directory:")
try:
    files = os.listdir(MODEL_PATH)
    for f in files:
        print(f" - {f}")
except Exception as e:
    print(f"Error listing files: {e}")

# Check critical files for SpeechT5
required = ["config.json", "pytorch_model.bin"]
missing = [f for f in required if f not in files]
if missing:
    print(f"WARNING: Potential missing model files: {missing}")

print("\n--- Attempting to Load Vocoder ---")
try:
    vocoder = SpeechT5HifiGan.from_pretrained(MODEL_PATH)
    print("SUCCESS: Vocoder loaded!")
except Exception as e:
    print(f"FAILURE: Vocoder load error:")
    traceback.print_exc()

print("\n--- Attempting to Initialize Pipeline ---")
try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    # Try fully bare pipeline first
    try:
        pipe = pipeline("text-to-speech", model=MODEL_PATH, vocoder=vocoder if 'vocoder' in locals() else None, device=device)
        print("SUCCESS: Pipeline initialized!")
        
        # Try generation
        print("Attempting generation...")
        # Random embedding test
        emb = torch.randn(1, 512).to(device)
        out = pipe("Hello World", forward_params={"speaker_embeddings": emb})
        print(f"SUCCESS: Audio generated! Shape: {out['audio'].shape}")
        
    except Exception as e:
        print(f"FAILURE: Pipeline error:")
        traceback.print_exc()

except Exception as e:
    print(f"FAILURE: General error: {e}")

print("\n--- END DIAGNOSTIC ---")
