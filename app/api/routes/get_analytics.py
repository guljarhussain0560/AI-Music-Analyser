# In your app/routers/songs.py or main.py file

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.dto import schemas # Assuming your DTOs are in schemas.py
from app.services import crud
from app.api.dependencies import get_db # Assuming get_db is in a dependencies file

# If you have a router, use it. Otherwise, use app = FastAPI()
router = APIRouter() 

@router.get("/songs/{song_id}", response_model=schemas.SongResponseDTO)
def read_song(song_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to retrieve a single song by its ID.
    """
    db_song = crud.get_song(db, song_id=song_id)
    if db_song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return db_song

# In your router file (e.g., app/routers/songs.py)

# Use the new DTO as the response_model
@router.get("/splits/bass/{song_id}", response_model=schemas.BassInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to retrieve only the bass audio splits for a given song ID.
    """
    db_split_data = crud.get_split_bass_info_by_song_id(db, song_id=song_id)
    
    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")

    # Manually map the tuple result to the Pydantic model
    # This is necessary because the query no longer returns a full object
    response_data = schemas.BassInfoDTO(
        bass_audio_url=db_split_data[0],
        bass_description=db_split_data[1]
    )
    
    return response_data

