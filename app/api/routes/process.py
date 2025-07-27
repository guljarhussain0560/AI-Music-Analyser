from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Query, HTTPException
from pathlib import Path
import uuid

from groq import BaseModel
from requests import Session

from app.db.database import SessionLocal
from app.services import audio_processing, crud

from app.services.audio_processing import (
    process_spotify_link,
    separate_audio_file
)

from app.utils.extract_lyrics import transcribe_lyrics
from app.utils.lyrics_aligner import rewrite_lyrics_with_timestamps

router = APIRouter()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SongRequest(BaseModel):
    url: str



@router.post("/split")
async def split_audio(file: UploadFile = File(...), prompt: str = Query(None)):

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




@router.post("/process_url")
def create_song_processing_job(
    song_request: SongRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # For this example, we assume a user with ID 1 exists.
    # In a real app, you would get this from an authentication system.
    user = crud.get_user(db, user_id=1)
    if not user:
        # In a real app, you would create the user or handle this case.
        raise HTTPException(status_code=404, detail="User with ID 1 not found.")

    # Add the long-running job to the background
    background_tasks.add_task(
        audio_processing.full_song_processing_pipeline, db, song_request.url, user.id
    )
    
    return {"message": "Song processing started in the background."}



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
