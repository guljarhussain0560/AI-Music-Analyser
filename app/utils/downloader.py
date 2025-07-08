import subprocess
import os
import uuid

def download_from_youtube(url: str, output_dir: str = "temp") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_dir, filename)

    command = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "-o", output_path,
        url
    ]
    subprocess.run(command, check=True)
    return output_path

def download_from_spotify(url: str, output_dir: str = "temp") -> str:
    os.makedirs(output_dir, exist_ok=True)
    command = ["spotdl", url, "--output", output_dir]
    subprocess.run(command, check=True)
    # Find the latest downloaded file
    files = os.listdir(output_dir)
    return os.path.join(output_dir, sorted(files)[-1])
