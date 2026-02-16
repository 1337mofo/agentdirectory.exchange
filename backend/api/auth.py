"""
Authentication & Authorization for Agent Directory
Admin API Key system for crawler automation
"""
from fastapi import Header, HTTPException, status
from typing import Optional
import os
import hashlib
import secrets

# Admin API key from environment
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", None)

# Fallback for development (will be overridden by environment variable)
if not ADMIN_API_KEY:
    print("[WARN]  WARNING: ADMIN_API_KEY not set in environment. Using development fallback.")
    ADMIN_API_KEY = "dev_eagle_admin_key_change_in_production"


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure comparison"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_admin_key() -> str:
    """Generate a new secure admin API key"""
    key = f"eagle_admin_{secrets.token_urlsafe(32)}"
    return key


async def verify_admin_api_key(
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    Verify admin API key from Authorization header
    
    Usage in endpoint:
        @app.post("/admin-endpoint")
        async def admin_function(authorized: bool = Depends(verify_admin_api_key)):
            # Only accessible with valid admin key
            ...
    
    Header format:
        Authorization: Bearer eagle_admin_XXXXXXXXXX
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    provided_key = authorization.replace("Bearer ", "").strip()
    
    if provided_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True


async def verify_optional_api_key(
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    Optional API key verification - returns True if valid, False if missing/invalid
    Use for endpoints that work better with auth but don't require it
    """
    if not authorization:
        return False
    
    if not authorization.startswith("Bearer "):
        return False
    
    provided_key = authorization.replace("Bearer ", "").strip()
    
    return provided_key == ADMIN_API_KEY


def get_api_key_info():
    """
    Get current API key configuration info (for debugging)
    DO NOT expose in production API - internal use only
    """
    return {
        "admin_key_configured": ADMIN_API_KEY is not None,
        "admin_key_length": len(ADMIN_API_KEY) if ADMIN_API_KEY else 0,
        "admin_key_prefix": ADMIN_API_KEY[:15] + "..." if ADMIN_API_KEY and len(ADMIN_API_KEY) > 15 else None,
        "source": "environment" if os.getenv("ADMIN_API_KEY") else "fallback"
    }


# Generate a new key on first import if needed
if __name__ == "__main__":
    print("\n🔑 Admin API Key Generator\n")
    print("Use this key for crawler automation and admin endpoints.\n")
    
    new_key = generate_admin_key()
    key_hash = hash_api_key(new_key)
    
    print(f"Generated Admin Key:")
    print(f"  {new_key}")
    print(f"\nKey Hash (for verification):")
    print(f"  {key_hash}")
    print(f"\nSet in environment:")
    print(f"  export ADMIN_API_KEY='{new_key}'  # Linux/Mac")
    print(f"  set ADMIN_API_KEY={new_key}       # Windows CMD")
    print(f"  $env:ADMIN_API_KEY='{new_key}'     # Windows PowerShell")
    print(f"\nOr add to Railway environment variables:")
    print(f"  ADMIN_API_KEY={new_key}")
    print(f"\n🔒 Keep this key secure! Do not commit to git.\n")
