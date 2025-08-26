import glob
import os
import re
import json
import logging
import subprocess

from spotdl import Spotdl

# --- SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
YT_COOKIES_PATH = os.getenv("YT_COOKIES_PATH")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

if not YT_COOKIES_PATH:
    logging.error("FATAL: Missing environment variable YT_COOKIES_PATH.")
    raise SystemExit("Configuration Error")

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    logging.error("FATAL: Missing environment variables for Spotify API.")
    raise SystemExit("Configuration Error")

# --- HELPER ---
def _sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

# --- DOWNLOAD FUNCTIONS ---
def download_from_youtube(url: str, output_dir: str) -> str:
    logging.info(f"-> Starting YouTube download for: {url}")
    os.makedirs(output_dir, exist_ok=True)
    try:
        info_command = ["yt-dlp", "--cookies", YT_COOKIES_PATH, "--dump-single-json", url]
        result = subprocess.run(info_command, check=True, capture_output=True, text=True, encoding='utf-8')
        info = json.loads(result.stdout)
        
        title = info.get('title', 'youtube_audio')
        sanitized_title = _sanitize_filename(title)
        output_template = os.path.join(output_dir, f"{sanitized_title}.%(ext)s")
        final_path = os.path.join(output_dir, f"{sanitized_title}.mp3")
        logging.info(f"   -> Saving as '{os.path.basename(final_path)}'")

        download_command = ["yt-dlp", "--cookies", YT_COOKIES_PATH, "-x", "--audio-format", "mp3", "-o", output_template, url]
        subprocess.run(download_command, check=True, capture_output=True)
        
        logging.info(f"   -> YouTube download successful: {final_path}")
        return final_path
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip()
        logging.error(f"❌ yt-dlp failed: {error_message}")
        raise ValueError(f"yt-dlp download failed: {error_message}") from e
    
    
    
downloader_settings = {
    "cookie_file": YT_COOKIES_PATH,
    "output": "{title} - {artist}.{output-ext}"
}

# Initialize Spotdl with the correct settings dictionary
spotdl_handler = Spotdl(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    headless=True,
    downloader_settings=downloader_settings
)

# Add asyncio to your imports at the top of the file
import os
import subprocess
import glob
from ytmusicapi import YTMusic
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def spotify_to_ytmusic_url(spotify_url: str) -> str:
    # 1. Get Spotify metadata
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET
    ))
    track_id = spotify_url.split("/")[-1].split("?")[0]
    track = sp.track(track_id)
    query = f"{track['name']} {track['artists'][0]['name']}"

    # 2. Search YouTube Music
    ytm = YTMusic()
    results = ytm.search(query, filter="songs")
    if results:
        return f"https://music.youtube.com/watch?v={results[0]['videoId']}"
    else:
        raise ValueError("No matching track found on YouTube Music")

def download_from_spotify(url: str, output_dir: str) -> str:
    """
    Downloads a song from Spotify by finding it on YouTube Music and then downloading the audio.
    """
    logging.info(f"-> Starting Spotify download for: {url}")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Convert Spotify URL to YouTube Music URL
        yt_url = spotify_to_ytmusic_url(url)
        logging.info(f"   -> Found YouTube Music URL: {yt_url}")

        # Get video info to create a sanitized filename
        info_command = ["yt-dlp", "--cookies", YT_COOKIES_PATH, "--dump-single-json", yt_url]
        result = subprocess.run(info_command, check=True, capture_output=True, text=True, encoding='utf-8')
        info = json.loads(result.stdout)
        
        title = info.get('title', 'spotify_audio')
        sanitized_title = _sanitize_filename(title)
        output_template = os.path.join(output_dir, f"{sanitized_title}.%(ext)s")
        final_path = os.path.join(output_dir, f"{sanitized_title}.mp3")
        logging.info(f"   -> Saving as '{os.path.basename(final_path)}'")


        # Download from YouTube Music using cookies
        download_command = [
            "yt-dlp",
            "--cookies", YT_COOKIES_PATH,  # Add this line
            "-x", # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0", # Best quality
            "-o", output_template,
            yt_url
        ]
        subprocess.run(download_command, check=True, capture_output=True)

        logging.info(f"   -> Spotify download successful: {final_path}")
        return final_path

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip()
        logging.error(f"❌ yt-dlp failed: {error_message}")
        raise ValueError(f"yt-dlp download failed: {error_message}") from e
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

