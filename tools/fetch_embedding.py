import torch
from datasets import load_dataset
import os
import sys

# Target Path
MODEL_DIR = r"C:\Users\Gary\models\canopyai\Orpheus-TTS"
EMBEDDING_PATH = os.path.join(MODEL_DIR, "speaker_embedding.pt")

if not os.path.exists(MODEL_DIR):
    print(f"Error: Model directory not found at {MODEL_DIR}")
    sys.exit(1)

print("Downloading speaker embeddings dataset (Matthijs/cmu-arctic-xvectors)...")
try:
    # Load dataset (small, just vectors)
    # trust_remote_code=True might be needed for older scripts
    embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation", trust_remote_code=True)
    
    # Select a speaker. 
    # Index 7306 is often used in examples (female voice 'slt'?)
    # Let's try to find a specific one or just pick one.
    # The dataset has feature 'xvector'.
    
    print("Selecting speaker embedding...")
    # Example index from generic tutorials is often 7306.
    # Let's verify size before saving.
    sample = embeddings_dataset[7306]
    speaker_embedding = torch.tensor(sample["xvector"]).unsqueeze(0)
    
    print(f"Check shape: {speaker_embedding.shape} (Should be [1, 512])")
    
    print(f"Saving to {EMBEDDING_PATH}...")
    torch.save(speaker_embedding, EMBEDDING_PATH)
    
    print("SUCCESS: Speaker embedding saved.")
    
except Exception as e:
    print(f"FAILURE: {e}")
