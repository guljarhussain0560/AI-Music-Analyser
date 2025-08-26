import os
import json
import requests
import time  # Import the time module for delays
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException
from pydub import AudioSegment
from app.utils.lyrics_aligner import rewrite_lyrics_with_timestamps
from app.utils.seg_to_lrc import convert_lyrics_to_lrc

print("🔧 Starting audio transcription service...")

# Load environment variables from .env
load_dotenv()
print("🔧 Loaded .env file")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

def transcribe_lyrics(audio_path: str, max_retries: int = 3) -> dict:
    """
    Transcribes audio using a direct API call to Groq's Whisper model,
    with a retry mechanism for server-side errors.
    """
    print("🎵 Audio Path:", audio_path)
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"❌ File not found: {audio_path}")

    # Convert WAV to optimized MP3 (mono, 16kHz, 32kbps) to reduce size
    if path.suffix.lower() == ".wav":
        print("🎤 Converting .wav to optimized .mp3...")
        mp3_path = path.with_suffix(".mp3")
        audio = AudioSegment.from_wav(path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(mp3_path, format="mp3", bitrate="32k")
    else:
        mp3_path = path

    # Log file size
    file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
    print(f"📦 File size: {file_size_mb:.2f} MB")

    api_url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    data_payload = {
        'model': 'whisper-large-v3',
        'response_format': 'verbose_json'
    }

    # --- EDITED SECTION: Added retry loop ---
    for attempt in range(max_retries):
        try:
            with open(mp3_path, "rb") as audio_file:
                print(f"🔊 Starting transcription... (Attempt {attempt + 1}/{max_retries})")
                
                files_payload = {
                    'file': (mp3_path.name, audio_file, 'audio/mpeg')
                }

                response = requests.post(api_url, headers=headers, data=data_payload, files=files_payload, timeout=300) # Added timeout
                response.raise_for_status()  # Raise an error for bad status codes (4xx or 5xx)
                
                print("✅ Transcription successful!")
                transcription_data = response.json()
                break  # Exit the loop on success

        except requests.exceptions.HTTPError as http_err:
            # Check if the error is a server-side error (500-599)
            if 500 <= http_err.response.status_code < 600:
                print(f"❌ Server error ({http_err.response.status_code}). Response: {http_err.response.text}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s...
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("❌ All retry attempts failed. Giving up.")
                    raise HTTPException(status_code=500, detail="Transcription failed after multiple retries due to API server error.")
            else:
                # It's a client-side error (e.g., 400, 401, 404), so don't retry
                print(f"❌ Client-side HTTP error: {http_err}")
                print(f"Response body: {http_err.response.text}")
                raise HTTPException(status_code=http_err.response.status_code, detail="Transcription failed due to a client-side API error.")
        
        except requests.exceptions.RequestException as req_err:
            # Handle other network errors like timeouts or connection errors
            print(f"❌ Network error during transcription: {req_err}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise HTTPException(status_code=500, detail="Transcription failed due to a persistent network error.")
    else:
        # This block runs if the loop completes without a `break`, which shouldn't happen with this logic, but is good for safety.
        raise HTTPException(status_code=500, detail="Transcription failed for an unknown reason after all retries.")
    # --- END EDITED SECTION ---
    
    # Process the JSON response dictionary
    language = transcription_data.get("language")
    duration = transcription_data.get("duration")
    print(f"🌐 Language: {language}")
    print(f"⏱️ Duration: {duration}")
    
    segments = [
        {
            "start": seg.get("start", 0.0),
            "end": seg.get("end", seg.get("start", 0.0) + 2.0),
            "text": seg.get("text", "").strip() or "."
        }
        for seg in transcription_data.get("segments", [])
    ]
    
    original_lrc = convert_lyrics_to_lrc(segments) 
    print(f"🎵 Original LRC:\n{original_lrc}")
    
    result = {
        "language": language,
        "duration": duration,
        "original_lrc": original_lrc
    }

    return result
