"""
Agent API Key Authentication System
Per-agent API keys for securing messaging, work orders, and payments
"""
from fastapi import HTTPException, Header, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import hashlib
from datetime import datetime
import uuid

from database.base import get_db
from models.agent import Agent


def generate_api_key(prefix: str = "eagle") -> str:
    """
    Generate a secure API key for an agent
    
    Format: eagle_live_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    
    Args:
        prefix: Key prefix (default: "eagle")
        
    Returns:
        str: Generated API key
    """
    random_part = secrets.token_urlsafe(32)  # 43 characters
    return f"{prefix}_live_{random_part}"


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage
    
    Args:
        api_key: Plain text API key
        
    Returns:
        str: SHA-256 hash of key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_agent(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Agent:
    """
    FastAPI dependency for agent authentication via API key
    
    Usage in endpoint:
        @router.post("/send-message")
        def send_message(agent: Agent = Depends(get_current_agent)):
            # agent is authenticated
            ...
    
    Header format:
        Authorization: Bearer eagle_live_XXXXXXXXXXXXX
    
    Raises:
        HTTPException: 401 if missing/invalid key, 403 if agent inactive
        
    Returns:
        Agent: Authenticated agent object
    """
    # Check Authorization header present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Include: Authorization: Bearer <your-api-key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format. Expected: Bearer <api-key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract API key
    api_key = authorization.replace("Bearer ", "").strip()
    
    # Validate key format (basic check)
    if not api_key.startswith("eagle_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find agent by API key
    agent = db.query(Agent).filter(Agent.api_key == api_key).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key - agent not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check agent is active
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent account is inactive. Contact support.",
        )
    
    # Update last_activity timestamp
    agent.last_activity_at = datetime.utcnow()
    db.commit()
    
    return agent


async def get_optional_agent(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[Agent]:
    """
    Optional agent authentication - returns None if not authenticated
    
    Use for endpoints that work better with auth but don't require it
    (e.g., public agent listings with authenticated filtering)
    """
    if not authorization:
        return None
    
    try:
        return await get_current_agent(authorization, db)
    except HTTPException:
        return None


def create_agent_with_api_key(
    name: str,
    description: str,
    owner_email: str,
    db: Session,
    **kwargs
) -> tuple[Agent, str]:
    """
    Create a new agent with API key
    
    Args:
        name: Agent name
        description: Agent description
        owner_email: Owner email address
        db: Database session
        **kwargs: Additional agent fields
        
    Returns:
        tuple: (Agent object, plain_api_key)
        
    Note: 
        API key is only returned once. Store it securely.
        Database stores hashed version only.
    """
    # Generate API key
    api_key = generate_api_key()
    
    # Create agent
    agent = Agent(
        name=name,
        description=description,
        owner_email=owner_email,
        api_key=api_key,  # Store plain key (for MVP - Phase 2: hash it)
        api_key_created_at=datetime.utcnow(),
        is_active=True,
        **kwargs
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return agent, api_key


def rotate_api_key(agent_id: uuid.UUID, db: Session) -> str:
    """
    Generate new API key for agent (invalidates old key)
    
    Args:
        agent_id: Agent UUID
        db: Database session
        
    Returns:
        str: New API key (plain text, only shown once)
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")
    
    # Generate new key
    new_api_key = generate_api_key()
    
    # Update agent
    agent.api_key = new_api_key
    agent.api_key_created_at = datetime.utcnow()
    
    db.commit()
    
    return new_api_key


# ============================================================================
# RATE LIMITING (Phase 1.5)
# ============================================================================

class RateLimitTier:
    """Rate limit tiers for different subscription levels"""
    FREE = {"messages_per_day": 100, "work_orders_per_day": 5}
    PRO = {"messages_per_day": 10000, "work_orders_per_day": 100}
    ENTERPRISE = {"messages_per_day": None, "work_orders_per_day": None}  # Unlimited


def check_rate_limit(agent: Agent, resource: str) -> bool:
    """
    Check if agent is within rate limits
    
    Args:
        agent: Authenticated agent
        resource: Resource type ("messages", "work_orders")
        
    Returns:
        bool: True if within limits
        
    Raises:
        HTTPException: 429 if rate limit exceeded
        
    TODO: Implement Redis-backed rate limiting in Phase 1.5
    For now, returns True (no limiting)
    """
    # Phase 1: No rate limiting (MVP)
    # Phase 1.5: Implement Redis counters
    return True


# ============================================================================
# TESTING & UTILITIES
# ============================================================================

def get_agent_auth_info(agent: Agent) -> dict:
    """
    Get authentication info for an agent (for debugging)
    DO NOT expose full API key in production
    """
    return {
        "agent_id": str(agent.id),
        "name": agent.name,
        "api_key_prefix": agent.api_key[:15] + "..." if agent.api_key else None,
        "api_key_created": agent.api_key_created_at.isoformat() if agent.api_key_created_at else None,
        "is_active": agent.is_active,
        "last_activity": agent.last_activity_at.isoformat() if agent.last_activity_at else None,
    }


if __name__ == "__main__":
    print("\n🔑 Agent API Key Generator\n")
    
    # Generate sample keys
    for i in range(3):
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        print(f"Agent {i+1}:")
        print(f"  API Key: {api_key}")
        print(f"  Hash: {key_hash[:16]}...")
        print()
    
    print("[OK] Use these keys for agent authentication")
    print("📝 Store keys securely - they're shown only once\n")
