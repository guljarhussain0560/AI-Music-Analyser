# app/api/routes/auth.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Assuming 'crud' is in the 'services' directory as per your imports
from app.services import crud 
from app.dto import schemas
from app.db.database import SessionLocal
from app.security import create_access_token, verify_password

# --- Load Environment Variables into Constants ONCE ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# --- Define Scheme ONCE ---
# The tokenUrl should point to the actual signin endpoint path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin") 

router = APIRouter()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Authentication Endpoints ---

@router.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/signin", response_model=schemas.Token)
def signin(user_credentials: schemas.UserCredentials, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=user_credentials.username)
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # BEST PRACTICE: Use user.id for the token subject
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=schemas.Token)
def google_auth(token: schemas.GoogleToken, db: Session = Depends(get_db)):
    try:
        id_info = id_token.verify_oauth2_token(
            token.credential, requests.Request(), GOOGLE_CLIENT_ID
        )

        email = id_info['email']
        name = id_info.get('name')
        # --- USE THE CORRECT FIELD NAME ---
        profile_picture_url = id_info.get('picture') 

    except ValueError:
        raise HTTPException(...) # Unchanged

    user = crud.get_user_by_email(db, email=email)
    if not user:
        user_in = schemas.UserCreate(
            email=email,
            username=email.split('@')[0],
            name=name,
            # --- USE THE CORRECT FIELD NAME ---
            profile_picture_url=profile_picture_url,
            password="dummypassword_from_google_signup"
        )
        user = crud.create_user(db, user_in)

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Dependency for Protected Routes ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # The subject 'sub' is now expected to be the user's ID
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Fetch user by their ID from the token
    user = crud.get_user(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
        
    return user



@router.get("/users/me", response_model=schemas.User)
def read_current_user(current_user: schemas.User = Depends(get_current_user)):
    """
    Fetches details for the currently authenticated user.
    """
    return current_user


