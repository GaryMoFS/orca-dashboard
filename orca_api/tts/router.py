import os
import time
import json
import hashlib
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from orca_api.events.router import manager

# Attempt to import pyttsx3 (DISABLED for stability)
HAS_PYTTSX3 = False
# try:
#     import pyttsx3
#     HAS_PYTTSX3 = True
# except ImportError:
#     HAS_PYTTSX3 = False

# Imports for Orpheus (SpeechT5)
from transformers import pipeline, SpeechT5HifiGan, SpeechT5Processor, SpeechT5ForTextToSpeech
import torch
import scipy.io.wavfile
import numpy as np

router = APIRouter()

class TTSRequest(BaseModel):
    run_id: str
    text: str
    voice_model: str = "orpheus"
    format: str = "wav"
    device_pref: str = "auto"

import subprocess
import sys

def run_probe_sync() -> dict:
    try:
        # Run independent process so crashes don't kill main server
        # Use sync subprocess.run which is robust
        res = subprocess.run(
            [sys.executable, "tools/probe_gpu.py"],
            capture_output=True, text=True, timeout=15 # Increased timeout for slow 5090 init
        )
        if res.returncode == 0 and res.stdout:
            return json.loads(res.stdout)
        else:
            return {"supported": False, "reason": "probe_process_failed", "stderr": res.stderr}
    except Exception as e:
        return {"supported": False, "reason": f"subprocess_error: {e}"}

async def run_probe_subprocess():
    return await asyncio.to_thread(run_probe_sync)

@router.get("/device_probe")
async def device_probe():
    return await run_probe_subprocess()

# Global TTS Pipeline (Lazy loaded)
TTS_PIPELINE = None
BASE_ORPHEUS_DIR = r"C:\Users\Gary\models\canopyai\Orpheus-TTS"

def get_tts_pipeline(device_pref="auto"):
    global TTS_PIPELINE
    
    # Check if we need to reload due to device mismatch
    if TTS_PIPELINE is not None:
        try:
            curr = TTS_PIPELINE.device.type # 'cuda' or 'cpu'
            if device_pref == "cuda" and curr != "cuda":
                print("Reloading TTS for CUDA Force...")
                TTS_PIPELINE = None
            elif device_pref == "cpu" and curr != "cpu":
                print("Reloading TTS for CPU...")
                TTS_PIPELINE = None
        except:
             pass

    if TTS_PIPELINE is None:
        # Check new separated structure first
        tts_path = os.path.join(BASE_ORPHEUS_DIR, "tts")
        vocoder_path = os.path.join(BASE_ORPHEUS_DIR, "vocoder")
        
        if not os.path.exists(tts_path): tts_path = BASE_ORPHEUS_DIR 
        
        if os.path.exists(tts_path):
            print(f"Loading Orpheus from {tts_path}...")
            try:
                # Device Logic
                if device_pref == "cuda":
                    print("Forcing CUDA usage (ignoring probe)...")
                    device = "cuda"
                elif device_pref == "cpu":
                    device = "cpu"
                else:
                    # Auto - use probe
                    try:
                        res = subprocess.run(
                            [sys.executable, "tools/probe_gpu.py"], 
                            capture_output=True, text=True, timeout=10
                        )
                        probe = json.loads(res.stdout)
                    except:
                        probe = {"supported": False, "reason": "timeout"}

                    if probe["supported"]:
                        device = "cuda"
                    else:
                        print(f"GPU unavailable: {probe['reason']}. Fallback CPU.")
                        device = "cpu"
                
                print(f"Device set to use {device}")
                
                # Load Vocoder
                vocoder = None
                if os.path.exists(vocoder_path):
                    try:
                        vocoder = SpeechT5HifiGan.from_pretrained(vocoder_path).to(device)
                        print("Local Vocoder loaded.")
                    except Exception as e:
                        print(f"Vocoder load failed: {e}")
                
                # Load TTS Pipeline
                if vocoder:
                    TTS_PIPELINE = pipeline("text-to-speech", model=tts_path, vocoder=vocoder, device=device)
                else:
                    TTS_PIPELINE = pipeline("text-to-speech", model=tts_path, device=device)
                    
            except Exception as e:
                print(f"Failed to load local model: {e}")
    return TTS_PIPELINE

def get_speaker_embedding(voice_id=""):
    # If a specific ID is requested like "orpheus:voice_3", load voice_3.pt
    if voice_id and voice_id.startswith("orpheus:"):
        parts = voice_id.split(":")
        if len(parts) > 1:
            fname = f"{parts[1]}.pt"
            path = os.path.join(BASE_ORPHEUS_DIR, "speakers", fname)
            if os.path.exists(path):
                return torch.load(path)

    # Fallback to random if no ID or file missing
    torch.manual_seed(42) 
    # Important: Normalize fallback too
    emb = torch.randn(1, 512)
    return torch.nn.functional.normalize(emb, p=2, dim=1)

def get_system_voices():
    """List available system voices + Orpheus Speakers"""
    voices_list = []
    
    # 1. Try Orpheus-FastAPI (Port 5005)
    try:
        import requests
        res = requests.get("http://127.0.0.1:5005/voices", timeout=2)
        if res.status_code == 200:
            data = res.json()
            for v in data.get("voices", []):
                 voices_list.append({"id": f"orpheus:{v}", "name": f"Orpheus (FastAPI) - {v.title()}"})
    except:
        pass

    # Orpheus Speakers (Local Fallback)
    spk_dir = os.path.join(BASE_ORPHEUS_DIR, "speakers")
    if os.path.exists(spk_dir):
        try:
            files = sorted(os.listdir(spk_dir))
            for f in files:
                if f.endswith(".pt"):
                    name = f.replace(".pt", "").replace("_", " ").title()
                    vid = f"orpheus:{f.replace('.pt', '')}"
                    voices_list.append({"id": vid, "name": f"Orpheus - {name}"})
        except:
            pass
            
    # Default Orpheus fallback
    if not voices_list and os.path.exists(BASE_ORPHEUS_DIR):
         voices_list.append({"id": "orpheus", "name": "Orpheus (Default)"})

    # System Voice Placeholder (Avoid pyttsx3 COM hangs)
    voices_list.append({"id": "system_default", "name": "System Default (SAPI5)"})
    
    return voices_list

def split_and_generate(pipe, text, speaker_embeddings, device):
    """
    Split long text into chunks (sentences), generate audio for each, 
    and concatenate them to handle SpeechT5 max token limits.
    """
    import re
    
    # Split by explicit punctuation
    # This regex splits but captures the delimiter, so we can re-attach.
    parts = re.split(r'([.!?]+)', text)
    
    chunks = []
    current = ""
    
    # Reassemble logic
    for part in parts:
        current += part
        # If we have a decent length chunk or it ends with punctuation, flush it
        # SpeechT5 context is ~600 tokens approx 400 chars maybe? Safe limit 300 chars.
        if len(current) > 300 or (len(current) > 50 and re.search(r'[.!?]+$', part)):
            if len(current.strip()) > 0:
                chunks.append(current.strip())
            current = ""
    
    if current.strip():
        chunks.append(current.strip())

    audio_segments = []
    sr = 16000 # SpeechT5 default
    
    for chunk in chunks:
        if not chunk: continue
        try:
            # forward_params must be passed specifically
            out = pipe(chunk, forward_params={"speaker_embeddings": speaker_embeddings})
            audio_segments.append(out["audio"])
            sr = out["sampling_rate"]
            
            # Add small silence gap? 
            # silence = np.zeros(int(sr * 0.1)) # 100ms
            # audio_segments.append(silence)
            
        except Exception as e:
            print(f"Chunk generation failed for '{chunk[:20]}...': {e}")
            
    if not audio_segments:
        return None
        
    # Concatenate
    final_audio = np.concatenate(audio_segments)
    return {"audio": final_audio, "sampling_rate": sr}

def generate_speech_file(text: str, output_path: str, voice_id: str = None, device_pref: str = "auto"):
    # 0. Try Orpheus-FastAPI (Primary)
    if not voice_id or "orpheus" in voice_id or voice_id in ["tara", "leo", "jess", "mia", "dan"]:
        try:
            import requests
            # Clean voice ID (e.g. "orpheus:tara" -> "tara")
            clean_voice = "tara"
            if voice_id and ":" in voice_id:
                clean_voice = voice_id.split(":")[1]
            elif voice_id and voice_id != "orpheus":
                 clean_voice = voice_id 

            # POST to /v1/audio/speech (returns WAV bytes)
            print(f"Proxying TTS request to Orpheus-FastAPI (Voice: {clean_voice})...")
            res = requests.post(
                "http://127.0.0.1:5005/v1/audio/speech",
                json={
                    "input": text,
                    "voice": clean_voice,
                    "model": "orpheus",
                    "response_format": "wav"
                },
                stream=True,
                timeout=120
            )
            
            if res.status_code == 200:
                abs_path = os.path.abspath(output_path)
                with open(abs_path, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=8192): 
                        f.write(chunk)
                return
            else:
                 print(f"Orpheus-FastAPI failed: {res.status_code} {res.text}")

        except Exception as e:
            print(f"Orpheus-FastAPI connection failed: {e}. Falling back to local pipeline.")

    # 1. Try Local Orpheus (if requested or id starts with 'orpheus')
    is_orpheus = (voice_id == "orpheus" or (voice_id and voice_id.startswith("orpheus:")))
    
    if is_orpheus and os.path.exists(BASE_ORPHEUS_DIR):
        pipe = get_tts_pipeline(device_pref)
        if pipe:
            try:
                speaker_embeddings = get_speaker_embedding(voice_id)
                # Ensure device match (we mandated cpu previously but just in case)
                if pipe.device.type == 'cuda':
                     speaker_embeddings = speaker_embeddings.to("cuda")
                
                # Check text length. If short (< 300 chars), just run.
                if len(text) < 300:
                    output = pipe(text, forward_params={"speaker_embeddings": speaker_embeddings})
                else:
                    # Long text -> Chunk Strategy
                    device = pipe.device
                    res = split_and_generate(pipe, text, speaker_embeddings, device)
                    if res:
                        output = res
                    else:
                        raise Exception("Chunking produced no audio")
                
                abs_path = os.path.abspath(output_path)
                scipy.io.wavfile.write(abs_path, rate=output["sampling_rate"], data=output["audio"])
                return 
            except Exception as e:
                import traceback
                print(f"[ORPHEUS ERROR] Generation failed:")
                traceback.print_exc()
                print(f"Falling back to System Voice...")

    # 2. Fallback...
    if HAS_PYTTSX3:
        engine = pyttsx3.init()
        if voice_id and voice_id != "orpheus":
            try:
                engine.setProperty('voice', voice_id)
            except:
                pass 
                
        abs_path = os.path.abspath(output_path)
        engine.save_to_file(text, abs_path)
        engine.runAndWait()
        del engine
    else:
        raise Exception("pyttsx3 not installed")

@router.get("/voices")
async def list_voices():
    # Run in thread to avoid blocking main loop
    voices = await asyncio.to_thread(get_system_voices)
    return {"voices": voices}

@router.post("/generate")
async def generate_speech(req: TTSRequest):
    # 1. Path Setup
    artifact_dir = f"runs/{req.run_id}/artifacts"
    os.makedirs(artifact_dir, exist_ok=True)
    
    ts_str = str(int(time.time()))
    filename = f"tts_output_{ts_str}.wav"
    file_path = f"{artifact_dir}/{filename}" 
    
    # 2. Generate Audio
    try:
        target_voice = req.voice_model if req.voice_model != "orpheus" else "orpheus"
        # Pass device_pref to thread
        await asyncio.to_thread(generate_speech_file, req.text, file_path, target_voice, req.device_pref)
    except Exception as e:
        if not os.path.exists(file_path):
             return {"status": "error", "message": str(e)}

    # 3. Read back stats
    try:
        with open(file_path, "rb") as f:
            wav_data = f.read()
            bytes_len = len(wav_data)
            sha256 = hashlib.sha256(wav_data).hexdigest()
    except:
        return {"status": "error", "message": "File generation failed"}

    # 4. Save Meta
    meta = {
        "provider": "local_tts",
        "model": req.voice_model,
        "text_snippet": req.text[:50],
        "sha256": sha256,
        "bytes": bytes_len,
        "created_ts": time.time()
    }
    with open(f"{file_path}.meta.json", "w") as f:
        json.dump(meta, f)
        
    # 5. Emit Event
    evt = {
        "type": "artifact.written",
        "run_id": req.run_id,
        "kind": "tts_output",
        "path": file_path.replace("\\", "/"),
        "sha256": sha256,
        "bytes": bytes_len
    }
    await manager.broadcast(json.dumps(evt))
    
    return {
        "status": "success",
        "audio_path": file_path.replace("\\", "/"),
        "model_used": req.voice_model
    }
