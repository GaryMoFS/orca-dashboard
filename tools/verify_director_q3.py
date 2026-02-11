import requests
import os
import io
import time
from PIL import Image, ImageDraw

RUNTIME_BASE = "http://127.0.0.1:7010"

def verify_q3():
    print("--- Verifying Q3 Director Quest Engine ---")
    
    # 1. Upload an image (Q2 dependency)
    print("Step 1: Uploading test image...")
    img = Image.new('RGB', (200, 100), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "QUEST TEST ASSET", fill=(255, 255, 0))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_data = img_byte_arr.getvalue()
    
    files = {'file': ('quest_test_sketch.png', img_data, 'image/png')}
    r = requests.post(f"{RUNTIME_BASE}/api/director/inbox/upload", files=files)
    r.raise_for_status()
    inbox_item = r.json()
    inbox_id = inbox_item['id']
    print(f"PASS: Uploaded image. Inbox ID: {inbox_id}")

    # 2. Create quest from inbox item
    print("Step 2: Creating quest from inbox item...")
    payload = {
        "inbox_id": inbox_id,
        "title": "Analyze Structural Sketch",
        "acceptance": "Verify beam spans and load points."
    }
    r = requests.post(f"{RUNTIME_BASE}/api/director/quests/from_inbox", json=payload)
    r.raise_for_status()
    quest = r.json()
    quest_id = quest['id']
    print(f"PASS: Quest created. Quest ID: {quest_id}")

    # 3. Move quest status to ACTIVE
    print("Step 3: Moving quest status to ACTIVE...")
    status_payload = {
        "quest_id": quest_id,
        "status": "active"
    }
    r = requests.post(f"{RUNTIME_BASE}/api/director/quests/set_status", json=status_payload)
    r.raise_for_status()
    print("PASS: Quest status set to ACTIVE")

    # 4. Confirm in quests list
    print("Step 4: Confirming quest in status list...")
    r = requests.get(f"{RUNTIME_BASE}/api/director/quests")
    r.raise_for_status()
    quests_data = r.json()
    if quest_id in quests_data['active']:
        print("PASS: Quest found in ACTIVE list.")
    else:
        print("FAIL: Quest not found in ACTIVE list.")

    # 5. Check events
    print("Step 5: Checking for events...")
    r = requests.get(f"{RUNTIME_BASE}/api/director/events?limit=10")
    r.raise_for_status()
    events = r.json()
    types = [e['type'] for e in events]
    if "quest.created" in types and "quest.status_changed" in types:
        print("PASS: Quest events emitted successfully.")
    else:
        print(f"FAIL: Missing events. Found: {types}")

if __name__ == "__main__":
    verify_q3()
