# app/api/routes/auth.py
import os
from fastapi import APIRouter, Depends, HTTPException, status
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests


from app.dto import schemas
from app.services import crud
from app.db.database import SessionLocal
from app.security import create_access_token, verify_password

load_dotenv()


router = APIRouter()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/signin", response_model=schemas.Token)
def signin(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=user_credentials.email)
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=schemas.Token)
def google_auth(token: schemas.GoogleToken, db: Session = Depends(get_db)):
    try:
        id_info = id_token.verify_oauth2_token(
            token.credential, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )
        email = id_info['email']
        name = id_info.get('name')
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    user = crud.get_user_by_email(db, email=email)
    if not user:
        # If user doesn't exist, create a new one with a dummy password
        # You might want to handle this differently, e.g., by asking them to set a password
        user_in = schemas.UserCreate(email=email, name=name, password="dummypassword_from_google_signup")
        user = crud.create_user(db, user_in)

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}