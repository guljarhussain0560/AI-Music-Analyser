from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Query, HTTPException
from pathlib import Path

from groq import BaseModel
from requests import Session

from app.services import audio_processing, crud
from app.api.dependencies import get_db


router = APIRouter()



class SongRequest(BaseModel):
    url: str
    
@router.post("/process_url")
def create_song_processing_job(
    song_request: SongRequest,
    # background_tasks is no longer needed here
    db: Session = Depends(get_db)
):
    # For this example, we assume a user with ID 1 exists.
    user = crud.get_user(db, user_id=1)
    if not user:
        raise HTTPException(status_code=404, detail="User with ID 1 not found.")

    # --- CHANGE IS HERE ---
    # Remove the background task and call the function directly.
    # The API will now wait for this function to finish.
    
    print("Starting synchronous song processing...")
    processing_results = audio_processing.full_song_processing_pipeline(
        db, song_request.url, user.id
    )
    
    if not processing_results:
        # Handle cases where the pipeline failed
        raise HTTPException(status_code=500, detail="Song processing failed.")

    # The function has finished, and we can now return its result.
    print(f"Processing complete. Returning IDs: {processing_results}")
    return processing_results



