from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.db.database import SessionLocal
from app.services import crud
from app.dto import schemas
from app.security import SECRET_KEY, ALGORITHM # Assuming these are in your security.py

# Dependency to get a DB session (can be reused from your auth.py)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# This defines that the token is expected at your /signin endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")

# This is the core dependency that will protect your endpoints
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # NOTE: Your /signin uses username, and /google uses email.
        # It's best to be consistent. This code assumes the JWT 'sub' is the user's email.
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user