"""
Database Base Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Create base class for models (doesn't need DB connection)
Base = declarative_base()

# Lazy initialization - only create engine when needed
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        # Database URL from environment variable
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/agent_marketplace"
        )
        _engine = create_engine(DATABASE_URL, echo=False)
    return _engine


def get_session_local():
    """Get or create session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """
    Dependency for FastAPI to get database session
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
