# app/crud.py
from sqlalchemy.orm import Session
from app.dto import schemas
from app.db import models
from app.security import get_password_hash

def create_song(db: Session,song: schemas.SongCreateDTO) -> models.Song:

    db_song = models.Song(
        title=song.title,
        owner_id=song.owner_id,
        song_url=song.song_url,
        lyrics=song.lyrics if song.lyrics is not None else {},
        description=song.description if song.description is not None else "",
    )
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        name=user.name,
        hashed_password=hashed_password,
        profile_picture_url=user.profile_picture_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_split(db: Session, split: schemas.SplitCreateDTO) -> models.Split:

    # Create an instance of the SQLAlchemy model from the Pydantic schema data
    db_split = models.Split(
        song_id=split.song_id,
        
        # URLs
        bass_audio_url=split.bass_audio_url,
        vocals_audio_url=split.vocals_audio_url,
        piano_audio_url=split.piano_audio_url,
        other_audio_url=split.other_audio_url,
        drum_audio_url=split.drum_audio_url,
        
        # Descriptions
        bass_description=split.bass_description,
        vocals_description=split.vocals_description,
        piano_description=split.piano_description,
        other_description=split.other_description,
        drum_description=split.drum_description,
        guitar_description=split.guitar_description,
        flute_description=split.flute_description,
        violin_description=split.violin_description
    )
    
    # Add the new object to the database session
    db.add(db_split)
    # Commit the transaction to save it to the database
    db.commit()
    # Refresh the object to get the newly generated ID
    db.refresh(db_split)
    
    return db_split

def get_song(db: Session, song_id: int):

    return db.query(models.Song).filter(models.Song.id == song_id).first()

def get_lyrics_by_song_id(db: Session, song_id: int):
    return db.query(models.Song.lyrics).filter(models.Song.id == song_id).first()

def get_split_by_song_id(db: Session, song_id: int):

    return db.query(models.Split).filter(models.Split.song_id == song_id).first()

def get_split_bass_info_by_song_id(db: Session, song_id: int):
    return db.query(
        models.Split.bass_audio_url,
        models.Split.bass_description
    ).filter(models.Split.id == song_id).first()
    
def get_split_piano_info_by_song_id(db: Session, song_id: int):
    return db.query(
        models.Split.piano_audio_url,
        models.Split.piano_description
    ).filter(models.Split.id == song_id).first()


def get_split_drum_info_by_song_id(db: Session, song_id: int):
    return db.query(
        models.Split.drum_audio_url,
        models.Split.drum_description
    ).filter(models.Split.id == song_id).first()


def get_split_other_info_by_song_id(db: Session, song_id: int):
    return db.query(
        models.Split.other_audio_url,
        models.Split.other_description
    ).filter(models.Split.id == song_id).first()


def get_split_vocals_info_by_song_id(db: Session, song_id: int):
    return db.query(
        models.Split.vocals_audio_url,
        models.Split.vocals_description
    ).filter(models.Split.id == song_id).first()


def get_split_guitar_info_by_song_id(db: Session, song_id: int):
    result = db.query(models.Split.guitar_description).filter(models.Split.id == song_id).first()

    return result[0] if result else None


def get_split_flute_info_by_song_id(db: Session, song_id: int):
    result = db.query(models.Split.flute_description).filter(models.Split.id == song_id).first()

    return result[0] if result else None


def get_split_violin_info_by_song_id(db: Session, song_id: int):
    result = db.query(models.Split.violin_description).filter(models.Split.id == song_id).first()

    return result[0] if result else None