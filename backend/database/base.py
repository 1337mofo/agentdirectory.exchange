"""
Database Base Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Create base class for models (doesn't need DB connection)
Base = declarative_base()

# Lazy initialization - only create engine when needed
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine with connection pooling"""
    global _engine
    if _engine is None:
        # Database URL from environment variable
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/agent_marketplace"
        )
        _engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_size=5,  # Limit concurrent connections
            max_overflow=10,  # Allow burst to 15 total
            pool_timeout=30,  # Wait 30s for available connection
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600  # Recycle connections after 1 hour
        )
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
    try:
        SessionLocal = get_session_local()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Continuing without database (check DATABASE_URL environment variable)")
        yield None


def get_db_connection():
    """
    Get raw psycopg2 database connection for protocol endpoints
    Used by protocol_endpoints, execution_tracking, performance_analytics, instrument_endpoints
    
    Returns None if connection fails (caller must handle)
    """
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            print("WARNING: DATABASE_URL not set, protocol endpoints will not work")
            return None
        
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        return None


def init_db():
    """
    Initialize database - create all tables
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
