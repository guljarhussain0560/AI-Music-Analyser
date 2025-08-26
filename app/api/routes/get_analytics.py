# In your app/routers/songs.py or main.py file

from urllib import response
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


@router.get("/splits/bass/{song_id}", response_model=schemas.BassInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_bass_info_by_song_id(db, song_id=song_id)
    
    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.BassInfoDTO(
        bass_audio_url=db_split_data[0],
        bass_description=db_split_data[1]
    )
    return response_data

@router.get("/splits/piano/{song_id}", response_model=schemas.PianoInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_piano_info_by_song_id(db, song_id=song_id)

    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.PianoInfoDTO(
        piano_audio_url=db_split_data[0],
        piano_description=db_split_data[1]
    )
    return response_data

@router.get("/splits/drums/{song_id}", response_model=schemas.DrumInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_drum_info_by_song_id(db, song_id=song_id)

    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.DrumInfoDTO(
        drum_audio_url=db_split_data[0],
        drum_description=db_split_data[1]
    )
    return response_data

@router.get("/splits/other/{song_id}", response_model=schemas.OtherInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_other_info_by_song_id(db, song_id=song_id)

    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.OtherInfoDTO(
        other_audio_url=db_split_data[0],
        other_description=db_split_data[1]
    )
    return response_data

@router.get("/splits/vocals/{song_id}", response_model=schemas.VocalsInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_vocals_info_by_song_id(db, song_id=song_id)

    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.VocalsInfoDTO(
        vocals_audio_url=db_split_data[0],
        vocals_description=db_split_data[1]
    )
    return response_data

@router.get("/splits/guitar/{song_id}", response_model=schemas.GuitarInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_guitar_info_by_song_id(db, song_id=song_id)

    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.GuitarInfoDTO(
        guitar_description=db_split_data
    )
    return response_data

@router.get("/splits/flute/{song_id}", response_model=schemas.FluteInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_flute_info_by_song_id(db, song_id=song_id)

    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.FluteInfoDTO(
        flute_description=db_split_data
    )
    return response_data

@router.get("/splits/violin/{song_id}", response_model=schemas.ViolinInfoDTO)
def read_splits_for_song(song_id: int, db: Session = Depends(get_db)):
    db_split_data = crud.get_split_violin_info_by_song_id(db, song_id=song_id)

    if db_split_data is None:
        raise HTTPException(status_code=404, detail="Splits for this song not found")
    response_data = schemas.ViolinInfoDTO(
        violin_description=db_split_data
    )
    return response_data