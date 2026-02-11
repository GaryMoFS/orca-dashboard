from transformers import pipeline
import torch
import scipy.io.wavfile
import os

MODEL_ID = "canopyai/Orpheus-TTS" # Or whatever the real ID is. try: "facebook/mms-tts-eng" or "microsoft/speecht5_tts" if this fails.

print(f"Attempting to load {MODEL_ID}...")

try:
    # Try to load as a pipeline
    # Note: If it's a specific architecture not supported by pipeline(), we might need specific classes.
    # Start with generic 'text-to-speech' pipeline.
    synthesiser = pipeline("text-to-speech", model=MODEL_ID, device="cuda" if torch.cuda.is_available() else "cpu")
    
    text = "Hello, I am Orpheus, running locally on your RTX 5090."
    print(f"Generating audio for: '{text}'")
    
    speech = synthesiser(text)
    
    # Save
    output_path = "orpheus_test.wav"
    scipy.io.wavfile.write(output_path, rate=speech["sampling_rate"], data=speech["audio"])
    
    print(f"SUCCESS: Audio saved to {os.path.abspath(output_path)}")
    
except Exception as e:
    print(f"FAILURE: {e}")
    print("\nIf the model ID is incorrect, try 'microsoft/speecht5_tts' or 'suno/bark-small'.")
