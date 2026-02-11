import requests
import os
import io
from PIL import Image, ImageDraw

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_q2():
    print("--- Verifying Q2 Director Inbox + OCR ---")
    
    # 1. Create a dummy image with some text
    img = Image.new('RGB', (200, 100), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    # Tesseract needs some contrast to read
    from PIL import ImageFont
    # Use default font if nothing else
    d.text((10, 10), "ORCA TEST ASSET", fill=(255, 255, 0))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_data = img_byte_arr.getvalue()
    
    # 2. Upload
    print("Uploading test image...")
    files = {'file': ('test_sketch.png', img_data, 'image/png')}
    try:
        r = requests.post(f"{RUNTIME_BASE}/api/director/inbox/upload", files=files)
        r.raise_for_status()
        item = r.json()
        inbox_id = item['id']
        print(f"PASS: Upload successful. Inbox ID: {inbox_id}")
    except Exception as e:
        print(f"FAIL: Upload failed: {e}")
        return

    # 3. Check artifacts
    print("Checking artifacts...")
    time_wait = 2 # Give it a second for OCR
    import time
    time.sleep(time_wait)
    
    try:
        # Check preview
        r = requests.get(f"{RUNTIME_BASE}/api/director/inbox/{inbox_id}/artifacts/derived/preview.jpg")
        r.raise_for_status()
        print(f"PASS: Preview artifact exists ({len(r.content)} bytes)")
        
        # Check OCR
        r = requests.get(f"{RUNTIME_BASE}/api/director/inbox/{inbox_id}/artifacts/derived/ocr.txt")
        r.raise_for_status()
        ocr_text = r.text.strip()
        print(f"PASS: OCR artifact exists. Content: '{ocr_text}'")
    except Exception as e:
        print(f"FAIL: Artifact check failed: {e}")

    # 4. List check
    try:
        r = requests.get(f"{RUNTIME_BASE}/api/director/inbox/list")
        r.raise_for_status()
        items = r.json()
        if any(i['id'] == inbox_id for i in items):
            print(f"PASS: Item found in inbox list.")
        else:
            print(f"FAIL: Item not found in list.")
    except Exception as e:
        print(f"FAIL: List check failed: {e}")

if __name__ == "__main__":
    verify_q2()
