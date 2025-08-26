# alembic/env.py

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool, create_engine

from alembic import context
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database URL from the environment variable
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL environment variable not set")

# --- This path fix is crucial ---
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# --- This import must find your models ---
from app.db.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Point Alembic to your models ---
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # This mode is not being used, so we can ignore it.
    url = "YOUR_HARDCODED_URL_HERE" # Placeholder
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # --- HARDCODE YOUR DATABASE URL FOR DEBUGGING ---
    # !!! REPLACE WITH YOUR REAL GOOGLE CLOUD CREDENTIALS !!!
    db_url = 
    
    # --- DEBUGGING PRINTS ---
    print("--- Simplified Alembic Run ---")
    print(f"1. Attempting to connect with URL: {db_url[:30]}...")
    print(f"2. Models found by Alembic: {list(target_metadata.tables.keys())}")


    connectable = create_engine(db_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            print("3. Running migrations...")
            context.run_migrations()
            print("4. Migrations complete.")


run_migrations_online()