"""
DEBUG ENDPOINTS - REMOVE AFTER FIXING
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from database.base import get_db

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])


@router.get("/db-test")
async def test_database(db: Session = Depends(get_db)):
    """Test database connection and query"""
    try:
        if db is None:
            return {
                "status": "error",
                "message": "Database session is None (get_db yielded None)",
                "DATABASE_URL": os.getenv("DATABASE_URL", "NOT SET")[:50] + "..."
            }
        
        # Try simple query
        result = db.execute(text("SELECT COUNT(*) FROM agents WHERE is_active = true")).scalar()
        
        return {
            "status": "success",
            "agent_count": result,
            "DATABASE_URL_set": os.getenv("DATABASE_URL") is not None,
            "db_session_valid": db is not None
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": str(type(e).__name__),
            "error_message": str(e),
            "DATABASE_URL_set": os.getenv("DATABASE_URL") is not None
        }


@router.get("/env-check")
async def check_environment():
    """Check environment variables"""
    return {
        "DATABASE_URL_exists": os.getenv("DATABASE_URL") is not None,
        "DATABASE_URL_preview": os.getenv("DATABASE_URL", "NOT SET")[:60] + "...",
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NOT SET"),
        "all_env_vars": list(os.environ.keys())[:20]  # First 20 env var names
    }
