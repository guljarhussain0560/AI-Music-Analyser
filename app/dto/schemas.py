# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Any, Dict, Optional

from sqlalchemy import JSON

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_active: bool = True


    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class GoogleToken(BaseModel):
    credential: str
    

class SongCreateDTO(BaseModel):
    title: str
    owner_id: int
    song_url: str
    lyrics: Optional[Dict[str, Any]] = {}
    description: Optional[Dict[str, Any]] = None
    
class SongResponseDTO(BaseModel):
    id: int
    title: str
    owner_id: int
    song_url: str
    lyrics: Dict[str, Any]
    description: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class SplitCreateDTO(BaseModel):
    song_id: int
    
    # URLs
    bass_audio_url: Optional[str] = None
    vocals_audio_url: Optional[str] = None
    piano_audio_url: Optional[str] = None
    other_audio_url: Optional[str] = None
    drum_audio_url: Optional[str] = None
    
    # Descriptions (JSONB fields are represented as Python dicts)
    bass_description: Optional[Dict[str, Any]] = None
    vocals_description: Optional[Dict[str, Any]] = None
    piano_description: Optional[Dict[str, Any]] = None
    other_description: Optional[Dict[str, Any]] = None
    drum_description: Optional[Dict[str, Any]] = None
    guitar_description: Optional[Dict[str, Any]] = None
    flute_description: Optional[Dict[str, Any]] = None
    violin_description: Optional[Dict[str, Any]] = None
    
class SplitResponseDTO(BaseModel):
    id: int
    song_id: int
    
    # URLs
    bass_audio_url: Optional[str] = None
    vocals_audio_url: Optional[str] = None
    piano_audio_url: Optional[str] = None
    other_audio_url: Optional[str] = None
    drum_audio_url: Optional[str] = None
    
    # Descriptions
    bass_description: Optional[Dict[str, Any]] = None
    vocals_description: Optional[Dict[str, Any]] = None
    piano_description: Optional[Dict[str, Any]] = None
    other_description: Optional[Dict[str, Any]] = None
    drum_description: Optional[Dict[str, Any]] = None
    guitar_description: Optional[Dict[str, Any]] = None
    flute_description: Optional[Dict[str, Any]] = None
    violin_description: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
        
        
class BassInfoDTO(BaseModel):
    bass_audio_url: Optional[str] = None
    bass_description: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
