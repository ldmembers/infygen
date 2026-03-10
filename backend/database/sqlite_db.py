"""
database/sqlite_db.py
SQLAlchemy engine, session factory, and DB initialisation.

Usage:
    from database.sqlite_db import get_db   # FastAPI dependency
    from database.sqlite_db import init_db  # call at startup
"""

from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings
from database.models import Base
from utils.logger import get_logger

logger = get_logger(__name__)

# Ensure the database directory exists
_db_path = Path(settings.database_url.replace("sqlite:///", ""))
_db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)
    logger.info("SQLite database initialised.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for non-FastAPI usage (workers, scripts)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
