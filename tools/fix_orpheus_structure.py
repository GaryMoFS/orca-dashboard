import os
import shutil
from huggingface_hub import snapshot_download

BASE_DIR = r"C:\Users\Gary\models\canopyai\Orpheus-TTS"
TTS_DIR = os.path.join(BASE_DIR, "tts")
VOCODER_DIR = os.path.join(BASE_DIR, "vocoder")

print(f"fixing Orpheus structure in {BASE_DIR}...")

# Create dirs
os.makedirs(TTS_DIR, exist_ok=True)
os.makedirs(VOCODER_DIR, exist_ok=True)

print("Downloading Microsoft SpeechT5 TTS to 'tts' subdir...")
snapshot_download(repo_id="microsoft/speecht5_tts", local_dir=TTS_DIR)

print("Downloading Microsoft SpeechT5 HiFi-GAN to 'vocoder' subdir...")
snapshot_download(repo_id="microsoft/speecht5_hifigan", local_dir=VOCODER_DIR)

print("SUCCESS: Files organized correctly.")
