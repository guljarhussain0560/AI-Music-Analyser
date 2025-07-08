from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from pathlib import Path
import uuid

from app.services.audio_processing import (
    process_spotify_link,
    process_youtube_link,
    separate_audio_file
)
from app.utils.extract_lyrics import transcribe_lyrics
from app.utils.lyrics_aligner import rewrite_lyrics_with_timestamps

router = APIRouter()

@router.post("/split")
async def split_audio(file: UploadFile = File(...), prompt: str = Query(None)):
    """
    Upload and split audio from a local file.
    Optionally rewrite lyrics using a custom prompt.
    """
    try:
        # Save uploaded file to temp directory
        unique_id = uuid.uuid4().hex
        input_path = Path(f"temp/{unique_id}_{file.filename}")
        input_path.parent.mkdir(parents=True, exist_ok=True)

        contents = await file.read()
        with open(input_path, "wb") as f:
            f.write(contents)

        # Prepare output directory
        output_dir = Path(f"output/{input_path.stem}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Separate audio into stems
        separate_audio_file(str(input_path), str(output_dir))

        # Optional: Transcribe and rewrite lyrics
        if prompt:
            vocals_path = output_dir / "vocals.wav"
            segments = transcribe_lyrics(str(vocals_path))
            rewritten = rewrite_lyrics_with_timestamps(segments, user_prompt=prompt)

            return {
                "status": "ok",
                "source": "file",
                "output_dir": str(output_dir),
                "lyrics": rewritten
            }

        return {"status": "ok", "source": "file", "output": str(output_dir)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/split/youtube")
def split_youtube_audio(url: str = Query(...), prompt: str = Query(None)):
    try:
        result = process_youtube_link(url)

        input_path = Path(result["input_path"])
        output_dir = Path(result["output_dir"])
        segments = result["lyrics"]

        #print("segments in process : ", segments)

        if prompt:
            rewritten = rewrite_lyrics_with_timestamps(segments, user_prompt=prompt)
            return {
                "status": "ok",
                "source": "youtube",
                "output_dir": str(output_dir),
                "lyrics": rewritten
            }

        return {
            "status": "ok",
            "source": "youtube",
            "output_dir": str(output_dir),
            "lyrics": segments
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print("❌ Route failed:", e)
        raise HTTPException(status_code=500, detail=str(e))

        
        

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print("❌ Route failed:", e)
        raise HTTPException(status_code=500, detail=str(e))





@router.post("/split/spotify")
def split_spotify_audio(url: str = Query(...), prompt: str = Query(None)):
    """
    Process Spotify audio and optionally rewrite lyrics using prompt.
    """
    try:
        input_path = Path(process_spotify_link(url))
        output_dir = Path(f"output/{input_path.stem}")
        output_dir.mkdir(parents=True, exist_ok=True)

        separate_audio_file(str(input_path), str(output_dir))

        if prompt:
            vocals_path = output_dir / "vocals.wav"
            segments = transcribe_lyrics(str(vocals_path))
            rewritten = rewrite_lyrics_with_timestamps(segments, user_prompt=prompt)

            return {
                "status": "ok",
                "source": "spotify",
                "output_dir": str(output_dir),
                "lyrics": rewritten
            }

        return {"status": "ok", "source": "spotify", "output": str(output_dir)}

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
