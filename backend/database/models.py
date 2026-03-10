"""
database/models.py
SQLAlchemy ORM models for SQLite metadata storage.

Tables:
  documents   — uploaded files and their ingestion metadata
  memory      — user-stored memories
  gmail_tokens — OAuth token storage per user
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(String(128), nullable=False, index=True)
    source_type = Column(String(32),  nullable=False)   # pdf | csv | txt | email | memory
    file_name   = Column(String(512), nullable=True)
    file_path   = Column(String(1024), nullable=True)
    chunk_count = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)
    indexed_at  = Column(DateTime, nullable=True)
    status      = Column(String(32), default="pending")  # pending | indexed | error
    error_msg   = Column(Text, nullable=True)


class Memory(Base):
    __tablename__ = "memory"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String(128), nullable=False, index=True)
    content    = Column(Text, nullable=False)
    faiss_id   = Column(Integer, nullable=True)   # index position in user's FAISS shard
    created_at = Column(DateTime, default=datetime.utcnow)


class GmailToken(Base):
    __tablename__ = "gmail_tokens"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(String(128), nullable=False, unique=True, index=True)
    token_json   = Column(Text, nullable=False)   # serialised google-auth token dict
    email        = Column(String(256), nullable=True)
    last_synced  = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
