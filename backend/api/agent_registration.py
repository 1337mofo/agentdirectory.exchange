"""
Agent Registration & API Key Management
Endpoints for agent signup and key rotation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

from database.base import get_db
from models.agent import Agent, AgentType, VerificationStatus
from api.agent_auth import (
    generate_api_key,
    rotate_api_key,
    get_current_agent,
    get_agent_auth_info
)


router = APIRouter(prefix="/api/v1/agents", tags=["Agent Registration"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class AgentRegistration(BaseModel):
    """Agent registration request"""
    name: str = Field(..., min_length=3, max_length=255, description="Agent name")
    description: str = Field(..., min_length=10, max_length=5000, description="Agent description")
    owner_email: EmailStr = Field(..., description="Owner email address")
    agent_type: AgentType = Field(default=AgentType.HYBRID, description="Agent type")
    capabilities: Optional[List[str]] = Field(default=[], description="Agent capabilities")
    website_url: Optional[str] = Field(None, max_length=500, description="Agent website/docs")
    contact_email: Optional[EmailStr] = Field(None, description="Public contact email")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Eagle Cost Analyst",
                "description": "AI agent specializing in cost estimation for product sourcing",
                "owner_email": "steve@theaerie.ai",
                "agent_type": "CAPABILITY",
                "capabilities": ["cost_estimation", "supplier_analysis", "market_research"],
                "website_url": "https://theaerie.ai/agents/cost-analyst",
                "contact_email": "eagle-cost-analyst@theaerie.ai"
            }
        }


class AgentRegistrationResponse(BaseModel):
    """Response after successful registration"""
    success: bool
    agent_id: str
    name: str
    api_key: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "agent_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Eagle Cost Analyst",
                "api_key": "eagle_live_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "message": "Agent registered successfully. Store your API key securely - it won't be shown again."
            }
        }


class ApiKeyRotationResponse(BaseModel):
    """Response after API key rotation"""
    success: bool
    new_api_key: str
    message: str
    rotated_at: str


class AgentAuthStatus(BaseModel):
    """Agent authentication status"""
    authenticated: bool
    agent_id: str
    name: str
    subscription_tier: str
    is_active: bool
    last_activity: Optional[str]
    api_key_created: Optional[str]


# ============================================================================
# REGISTRATION ENDPOINTS
# ============================================================================

@router.post("/register", response_model=AgentRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    registration: AgentRegistration,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new agent and receive API key
    
    **Anti-Abuse Protection:**
    - 50 free calls total
    - 5 calls/hour refill rate
    - Max 5 signups per IP per day
    - Disposable email blocking
    - Platform-wide $50/day free tier cap
    
    **Important:** API key is shown only once. Store it securely.
    
    Process:
    1. Submit registration details
    2. Receive agent_id and api_key
    3. Use api_key in Authorization header for all requests
    
    Example:
    ```
    Authorization: Bearer eagle_live_XXXXXXXXXXXXX
    ```
    """
    from api.rate_limiting import (
        get_client_ip,
        check_ip_signup_limit,
        record_ip_signup,
        is_disposable_email,
        check_daily_spending_cap
    )
    
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Check IP signup limit (5 per day)
    ip_allowed = await check_ip_signup_limit(client_ip, db)
    if not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signups from this IP address today. Limit: 5 signups per day. Try again tomorrow."
        )
    
    # Check disposable email
    is_disposable = await is_disposable_email(registration.owner_email, db)
    if is_disposable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disposable email addresses are not allowed. Please use a permanent email address."
        )
    
    # Check daily platform spending cap
    cap_ok = await check_daily_spending_cap(db)
    if not cap_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Daily free tier capacity reached. Please try again tomorrow or purchase paid credits."
        )
    
    # Check if agent name already exists
    existing = db.query(Agent).filter(Agent.name == registration.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent name '{registration.name}' is already registered"
        )
    
    # Generate API key
    api_key = generate_api_key()
    
    # Create agent with rate limiting defaults
    agent = Agent(
        name=registration.name,
        description=registration.description,
        agent_type=registration.agent_type,
        owner_email=registration.owner_email,
        capabilities=registration.capabilities or [],
        api_key=api_key,
        api_key_created_at=datetime.utcnow(),
        is_active=True,
        verification_status=VerificationStatus.UNVERIFIED,
        subscription_tier="free",
        source_url=registration.website_url,
        owner_user_id=None,  # TODO: Link to user accounts in Phase 2
        # Anti-abuse rate limiting
        free_calls_total=50,
        free_calls_remaining=50,
        hourly_rate_limit=5,
        hourly_calls_count=0,
        hourly_reset_at=datetime.utcnow(),
        signup_ip_address=client_ip,
        daily_spending_exposure=0.0,
        paid_calls_remaining=0
    )
    
    # Set contact email if provided
    if registration.contact_email:
        agent.extra_data = {"contact_email": registration.contact_email}
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    # Record IP signup
    await record_ip_signup(client_ip, db)
    
    return AgentRegistrationResponse(
        success=True,
        agent_id=str(agent.id),
        name=agent.name,
        api_key=api_key,
        message="Agent registered successfully. You have 50 free calls (5 calls/hour). Store your API key securely - it won't be shown again."
    )


@router.post("/rotate-key", response_model=ApiKeyRotationResponse)
def rotate_agent_key(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Rotate API key (invalidates old key)
    
    Requires: Valid current API key in Authorization header
    
    Returns: New API key (shown only once)
    
    **Warning:** Old API key stops working immediately.
    Update all systems using the old key.
    """
    # Generate new key
    new_api_key = rotate_api_key(agent.id, db)
    
    return ApiKeyRotationResponse(
        success=True,
        new_api_key=new_api_key,
        message="API key rotated successfully. Old key is now invalid.",
        rotated_at=datetime.utcnow().isoformat()
    )


# ============================================================================
# AUTHENTICATION STATUS
# ============================================================================

@router.get("/auth-status", response_model=AgentAuthStatus)
def check_auth_status(agent: Agent = Depends(get_current_agent)):
    """
    Check authentication status
    
    Requires: Valid API key in Authorization header
    
    Returns: Agent info and authentication details
    
    Use this endpoint to:
    - Verify API key is valid
    - Check subscription tier
    - Confirm agent is active
    """
    return AgentAuthStatus(
        authenticated=True,
        agent_id=str(agent.id),
        name=agent.name,
        subscription_tier=agent.subscription_tier,
        is_active=agent.is_active,
        last_activity=agent.last_activity_at.isoformat() if agent.last_activity_at else None,
        api_key_created=agent.api_key_created_at.isoformat() if agent.api_key_created_at else None
    )


@router.get("/me")
def get_my_agent(agent: Agent = Depends(get_current_agent)):
    """
    Get authenticated agent's full profile
    
    Requires: Valid API key in Authorization header
    
    Returns: Complete agent object (same as /agents/{agent_id})
    """
    return agent.to_dict()


@router.get("/rate-limits")
async def get_rate_limits(agent: Agent = Depends(get_current_agent)):
    """
    Get current rate limit status
    
    Returns:
    - Free credits remaining
    - Paid credits remaining
    - Hourly limit status
    - Time until reset
    - Upgrade recommendation
    
    Use this to display rate limit info in your agent's dashboard
    """
    from api.rate_limiting import get_rate_limit_info
    
    return get_rate_limit_info(agent)


# ============================================================================
# TESTING ENDPOINT (Remove in production)
# ============================================================================

@router.post("/test-register", include_in_schema=False)
def test_register_agent(name: str, email: str, db: Session = Depends(get_db)):
    """
    Quick registration for testing (no validation)
    **REMOVE THIS IN PRODUCTION**
    """
    api_key = generate_api_key()
    
    agent = Agent(
        name=name,
        description=f"Test agent: {name}",
        agent_type=AgentType.HYBRID,
        owner_email=email,
        api_key=api_key,
        api_key_created_at=datetime.utcnow(),
        is_active=True,
        verification_status=VerificationStatus.UNVERIFIED,
        subscription_tier="free"
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return {
        "agent_id": str(agent.id),
        "name": agent.name,
        "api_key": api_key,
        "message": "TEST ONLY - Remove this endpoint in production"
    }
