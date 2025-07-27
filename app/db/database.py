# db/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .base import Base

# --- Part 1: Session Setup

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Important: SQLAlchemy 2.0 requires the driver to be specified.
# The URL from Railway is postgresql://..., but psycopg2 needs postgresql+psycopg2://...
if DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


from .models import User, Song, Split

# --- Part 3: Database Initialization (from init_db.py) ---

def init_db():
    """
    Initializes the database by creating all tables defined in the models.
    """
    print("Creating all database tables...")
    # The models are imported above, so Base.metadata knows about them.
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

# This allows you to run `python -m db.database` to initialize the DB
if __name__ == "__main__":
    init_db()      