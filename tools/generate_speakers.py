import torch
import os

BASE_DIR = r"C:\Users\Gary\models\canopyai\Orpheus-TTS"
SPEAKERS_DIR = os.path.join(BASE_DIR, "speakers")

os.makedirs(SPEAKERS_DIR, exist_ok=True)

print(f"Generating random speaker embeddings in {SPEAKERS_DIR}...")

# Generate 10 variations
for i in range(1, 11):
    # Use different seeds to get different voice characteristics
    seed = 42 + i * 100 
    torch.manual_seed(seed)
    
    # Generate random xvector (1, 512)
    # Normalize it? SpeechT5 xvectors are usually normalized.
    # Let's try standard normal distribution.
    emb = torch.randn(1, 512)
    
    # Normalize to unit length (improves stability/reduces static?)
    # Xvectors are often cosine-similarity based, so unit norm helps.
    emb = torch.nn.functional.normalize(emb, p=2, dim=1)
    
    filename = f"voice_{i}.pt"
    path = os.path.join(SPEAKERS_DIR, filename)
    torch.save(emb, path)
    print(f" - Saved {filename}")

print("Done! Restart backend to see them in settings.")
