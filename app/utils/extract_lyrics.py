import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException
from groq import Groq
from pydub import AudioSegment
from app.utils.lyrics_aligner import rewrite_lyrics_with_timestamps

print("🔧 Starting extract_lyrics.py")  # Debug

# Load environment variables from .env
load_dotenv()
print("🔧 Loaded .env file")  # Debug

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print(f"🔧 GROQ_API_KEY: {GROQ_API_KEY}")  # Debug

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)
print("🔧 Groq client initialized")  # Debug

def transcribe_lyrics(audio_path: str) -> list:
    print("🎵 Audio Path:", audio_path)
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"❌ File not found: {audio_path}")

    # Convert WAV to optimized MP3 (mono, 16kHz, 32kbps) to reduce size
    if path.suffix.lower() == ".wav":
        mp3_path = path.with_suffix(".mp3")
        audio = AudioSegment.from_wav(path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        # Optional: Trim to first 30 seconds for testing
        # audio = audio[:30_000]
        
        audio.export(mp3_path, format="mp3", bitrate="32k")
    else:
        mp3_path = path

    # Log file size
    file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
    print(f"📦 File size: {file_size_mb:.2f} MB")

    try:
        with open(mp3_path, "rb") as audio_file:
            print("🔊 Starting transcription...")
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                response_format="verbose_json"
            )
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed due to timeout or format error")

    print(f"🌐 Detected language: {transcription.language}")

    segments = [
        {
            "start": seg.get("start", 0.0),
            "end": seg.get("end", seg.get("start", 0.0) + 2.0),
            "text": seg.get("text", "").strip() or "."
        }
        for seg in transcription.segments
    ]

    print("✅ Transcription completed. Segments extracted:")
    for seg in segments[:20]:  # Show only first 20 for brevity
        print(seg)

    return transcription.segments
