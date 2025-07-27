import http.client
import json
import time
import requests

# === CONFIGURATION ===
API_TOKEN = "Bearer 320569a8935dcd80d9b63a765a2c23db"  # 🔁 Replace with your actual API token
CALLBACK_URL = "https://example.com/dummy"  # Required but doesn't need to work

# === SONG INPUT ===
prompt = """Generate a hindi language song  an uplifting, energetic, and triumphant music prompt with a strong emphasis on Indian cultural vibes, blending elements of electronic, pop, and inspirational sports anthem styles. Imagine a track that pulses with the excitement of a packed stadium, featuring a dynamic mix of traditional Indian instruments like the tabla and sitar, alongside modern electronic beats, soaring synth pads, and a driving rhythm section, including powerful drums and bass. The melody should evoke a sense of national pride and unity, with celebratory horns and strings adding to the euphoric atmosphere. The music should build from an intense, motivational anthem to a joyous, chant"""
style = "Epic Cinematic"
title = "Sons 3"
model = "V4_5"  # Or "V4", "V3_5"

# === STEP 1: Send music generation request ===
print("🎶 Sending music generation request...")

conn = http.client.HTTPSConnection("api.sunoapi.org")

payload = json.dumps({
    "prompt": prompt,
    "style": style,
    "title": title,
    "customMode": True,
    "instrumental": False,
    "model": model,
    "negativeTags": "Heavy Metal, Screaming",
    "callBackUrl": CALLBACK_URL
})

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': API_TOKEN
}

conn.request("POST", "/api/v1/generate", payload, headers)
res = conn.getresponse()
data = res.read()
response_json = json.loads(data.decode("utf-8"))
conn.close()

# === STEP 2: Extract taskId ===
task_data = response_json.get("data")
if not task_data or "taskId" not in task_data:
    print("❌ Task creation failed:", response_json)
    exit()

task_id = task_data["taskId"]
print(f"✅ Task created: {task_id}")

# === STEP 3: Poll /generate/record-info ===
def poll_task_info(task_id):
    print("⏳ Polling for song generation status...")
    while True:
        conn = http.client.HTTPSConnection("api.sunoapi.org")
        headers = {
            'Accept': 'application/json',
            'Authorization': API_TOKEN
        }
        conn.request("GET", f"/api/v1/generate/record-info?taskId={task_id}", headers=headers)
        res = conn.getresponse()
        result = json.loads(res.read().decode("utf-8"))
        conn.close()

        data = result.get("data", {})
        status = data.get("status")

        print(f"🔄 Status: {status}")
        if status == "SUCCESS":
            return data
        elif status in ["FAILED", "CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED"]:
            raise Exception(f"❌ Song generation failed: {status}")
        time.sleep(5)

# Wait for completion
song_info = poll_task_info(task_id)

# === STEP 4: Extract and Download MP3 from nested response ===
try:
    audio_url = song_info["response"]["sunoData"][0]["audioUrl"]
except (KeyError, IndexError, TypeError):
    audio_url = None

if audio_url:
    print(f"🎧 Downloading song from: {audio_url}")
    audio = requests.get(audio_url).content
    filename = title.replace(" ", "_").lower() + ".mp3"
    with open(filename, "wb") as f:
        f.write(audio)
    print(f"✅ Song saved as: {filename}")
else:
    print("❌ audioUrl not found in song_info['response']['sunoData'][0]")

