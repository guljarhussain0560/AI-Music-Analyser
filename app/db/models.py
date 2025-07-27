# db/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

# All models will inherit from this Base.
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    profile_picture_url = Column(String, nullable=True)


    # Establishes a one-to-many relationship to the Song model
    songs = relationship("Song", back_populates="owner", cascade="all, delete-orphan")


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True , nullable=False, default="Untitled")
    song_url = Column(String, nullable=False)
    lyrics = Column(JSONB, nullable=False)
    description = Column(JSONB, nullable=True)
    
    # Foreign key to the users table
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Establishes the many-to-one relationship with the User model
    owner = relationship("User", back_populates="songs")

    # Establishes the one-to-many relationship with the Split model
    splits = relationship("Split", back_populates="song", cascade="all, delete-orphan")


class Split(Base):
    __tablename__ = "splits"

    id = Column(Integer, primary_key=True, index=True)
    
    #bass
    bass_audio_url = Column(String, nullable=True)
    bass_description = Column(JSONB, nullable=True)

    #vocal
    vocals_audio_url = Column(String, nullable=True)
    vocals_description = Column(JSONB, nullable=True)
    
    #piano
    piano_audio_url = Column(String, nullable=True)
    piano_description = Column(JSONB, nullable=True)

    #other instruments
    other_audio_url = Column(String, nullable=True)
    other_description = Column(JSONB, nullable=True)

    #drum
    drum_audio_url = Column(String, nullable=True)
    drum_description = Column(JSONB, nullable=True)
    
    #guitar descriptions
    guitar_description = Column(JSONB, nullable=True)

    #flute descriptions
    flute_description = Column(JSONB, nullable=True)
    
    #violin descriptions
    violin_description = Column(JSONB, nullable=True)

    # Foreign key to link back to the parent song
    song_id = Column(Integer, ForeignKey("songs.id"))

    # Establishes the many-to-one relationship with the Song model
    song = relationship("Song", back_populates="splits")