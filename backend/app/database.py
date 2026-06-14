"""Database engine and session configuration.

Defaults to a local SQLite file so the project runs with zero extra setup.
Set the DATABASE_URL environment variable to point at Postgres instead, e.g.:

    DATABASE_URL=postgresql://edr:edr@localhost:5432/edr
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./mini_edr.db")

# SQLite needs this flag when used from multiple threads (FastAPI's default
# thread pool for sync endpoints).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
