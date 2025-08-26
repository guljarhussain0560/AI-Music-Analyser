import os
import shutil
import tempfile
from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile, File, Query, HTTPException
from pathlib import Path

from pydantic import BaseModel
from requests import Session

from app.services import audio_processing, crud
from app.api.dependencies import get_db
from app.utils.lyrics_aligner import rewrite_lyrics_with_timestamps


router = APIRouter()



class SongRequest(BaseModel):
    url: str
    id: int
    
@router.post("/process_url")
def create_song_processing_job(
    song_request: SongRequest,
    # background_tasks is no longer needed here
    db: Session = Depends(get_db)
):
    # For this example, we assume a user with ID 1 exists.
    print(f"Received song request for URL: {song_request.url}")
    print("Fetching user with ID :", song_request.id)
    user = crud.get_user(db, user_id=song_request.id)
    if not user:
        raise HTTPException(status_code=404, detail="User with ID 1 not found.")

    # --- CHANGE IS HERE ---
    # Remove the background task and call the function directly.
    # The API will now wait for this function to finish.
    
    print("Starting synchronous song processing...")
    processing_results = audio_processing.full_song_processing_pipeline(
        db, song_request.url, song_request.id
    )
    
    if not processing_results:
        # Handle cases where the pipeline failed
        raise HTTPException(status_code=500, detail="Song processing failed.")

    # The function has finished, and we can now return its result.
    print(f"Processing complete. Returning IDs: {processing_results}")
    return processing_results



@router.post("/process_audio_file")
def create_song_processing_job_from_file(
    # FastAPI handles multipart/form-data when you use File() and Form()
    user_id: int = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Receives an audio file and a user_id, processes the song,
    and returns the results.
    """
    print(f"Received audio file upload: '{audio_file.filename}' for user ID: {user_id}")
    
    # 1. Fetch the user from the database (same as before)
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")

    # 2. Save the uploaded audio file to a temporary location on the server
    # This is necessary because our processing pipeline needs a file path to work with.
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, audio_file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        print(f"Audio file saved temporarily to: {temp_file_path}")

        # 3. Call a new processing pipeline that works with a local file path
        print("Starting synchronous song processing from file...")
        
        # NOTE: You will need to create this new function in your audio_processing module.
        # It will be very similar to 'full_song_processing_pipeline' but will skip the download step.
        processing_results = audio_processing.process_audio_file_pipeline(
            db=db, 
            file_path=temp_file_path, 
            user_id=user_id
        )
        
        if not processing_results:
            raise HTTPException(status_code=500, detail="Song processing from file failed.")

        # 4. Return the results (same as before)
        print(f"Processing complete. Returning IDs: {processing_results}")
        return processing_results

    finally:
        # 5. Clean up: always remove the temporary directory and its contents
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        
        # Close the uploaded file
        audio_file.file.close()



@router.get("/get-lyrics/{song_id}", response_model=dict)
def get_lyrics(
    song_id: int,
    db: Session = Depends(get_db)
):
    song = crud.get_lyrics_by_song_id(db, song_id=song_id)
    print("Song fetched:", song)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    return song.lyrics if song.lyrics else {}


class RewriteRequest(BaseModel):
    prompt: str

@router.post("/rewrite-lyrics/{song_id}", response_model=dict)
async def create_lyrics_rewrite(
    song_id: int,
    request: RewriteRequest,
    db: Session = Depends(get_db)
):
    # 1. Fetch the song from the database using your CRUD function
    song = crud.get_lyrics_by_song_id(db, song_id=song_id)

    if not song:
        raise HTTPException(status_code=404, detail=f"Song with ID '{song_id}' not found")

    # 2. Call the AI function with the original lyrics and the user's prompt
    duration = song.lyrics.get('duration', 0.0)
    language = song.lyrics.get('language', 'en')
    lyrics = song.lyrics.get('original_lrc', '')

    new_lyrics = rewrite_lyrics_with_timestamps(
        lrc_string=lyrics,
        language=language,
        duration=duration,
        user_prompt=request.prompt
    )

    # 3. Return the newly generated lyrics
    return {"lyrics": new_lyrics}
