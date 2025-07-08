from pathlib import Path
from uuid import uuid4
from app.utils.spleeter_wrapper import spleeter_split
from app.utils.downloader import download_from_youtube, download_from_spotify
from app.utils.extract_lyrics import transcribe_lyrics


def separate_audio_file(input_path: str, output_dir: str):
    print(f"[DEBUG] separate_audio_file called with input_path={input_path}, output_dir={output_dir}")
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    split_result = spleeter_split(str(input_path), str(output_dir_path))
    vocal_path = Path(split_result["vocals"])
    if not vocal_path.exists():
        raise FileNotFoundError(f"Vocals file not found at: {vocal_path}")

    lyrics = transcribe_lyrics(str(vocal_path))

    return {
        "output_dir": str(output_dir_path),
        "vocals_path": str(vocal_path),
        "lyrics": lyrics,
    }


def process_youtube_link(youtube_url: str):
    print(f"[DEBUG] process_youtube_link called with youtube_url={youtube_url}")
    input_path = Path(download_from_youtube(youtube_url))  # e.g., temp/abc123.mp3
    output_dir = Path("output") / f"youtube_{input_path.stem}"

    # Run Spleeter and get output paths
    split_result = spleeter_split(str(input_path), str(output_dir))

    vocal_path = Path(split_result["vocals"])
    if not vocal_path.exists():
        raise FileNotFoundError(f"Vocals file not found at: {vocal_path}")

    lyrics = transcribe_lyrics(str(vocal_path))

    return {
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "vocals": str(vocal_path),
        "lyrics": lyrics
    }





def process_spotify_link(spotify_url: str):
    print(f"[DEBUG] process_spotify_link called with spotify_url={spotify_url}")
    try:
        input_path = Path(download_from_spotify(spotify_url))
    except Exception as e:
        raise RuntimeError(f"Spotify download failed: {e}")

    if not input_path.exists():
        raise FileNotFoundError(f"Downloaded file not found: {input_path}")

    output_dir = Path("output") / f"spotify_{input_path.stem}_{uuid4().hex[:8]}"
    print(f"[🎧] Splitting audio at: {output_dir}")

    split_result = spleeter_split(str(input_path), str(output_dir))

    if "vocals" not in split_result:
        raise RuntimeError("Spleeter failed to extract vocals.")

    vocal_path = Path(split_result["vocals"])
    if not vocal_path.exists():
        raise FileNotFoundError(f"Vocals file not found at: {vocal_path}")

    print(f"[🧠] Transcribing vocals...")
    lyrics = transcribe_lyrics(str(vocal_path))

    return {
        "output_dir": str(output_dir),
        "vocals_path": str(vocal_path),
        "lyrics": lyrics,
    }
