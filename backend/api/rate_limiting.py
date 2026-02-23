"""
Anti-Abuse Rate Limiting System
Implements Boots' strategy: 50 free calls total, 5 calls/hour refill, IP limits
"""
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
import ipaddress

from models.agent import Agent
from database.base import get_db


# ============================================================================
# RATE LIMITING CONSTANTS
# ============================================================================

FREE_CALLS_TOTAL = 50  # Total free calls per agent
HOURLY_RATE_LIMIT = 5  # Calls per hour refill rate
MAX_SIGNUPS_PER_IP_PER_DAY = 5  # IP-based signup limit
DAILY_SPENDING_CAP_USD = 50.0  # Platform-wide daily free tier cap
AVERAGE_CALL_COST_USD = 0.005  # Average tool cost for exposure calculation


# ============================================================================
# IP TRACKING & VALIDATION
# ============================================================================

def get_client_ip(request: Request) -> str:
    """
    Extract real client IP from request (handles proxies/load balancers)
    
    Checks headers in priority order:
    1. X-Forwarded-For (most common)
    2. X-Real-IP (nginx)
    3. CF-Connecting-IP (Cloudflare)
    4. request.client.host (direct connection)
    """
    # Check proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


def is_private_ip(ip_address: str) -> bool:
    """Check if IP is private/local (exempt from rate limiting)"""
    try:
        ip = ipaddress.ip_address(ip_address)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


async def check_ip_signup_limit(ip_address: str, db: Session) -> bool:
    """
    Check if IP has exceeded daily signup limit (5 per day)
    
    Args:
        ip_address: Client IP address
        db: Database session
        
    Returns:
        bool: True if within limit, False if exceeded
    """
    # Skip check for private IPs (development)
    if is_private_ip(ip_address):
        return True
    
    today = datetime.utcnow().date()
    
    # Check existing tracking record
    from sqlalchemy import text
    
    result = db.execute(
        text("""
            SELECT signup_count FROM ip_signup_tracking 
            WHERE ip_address = :ip AND signup_date = :date
        """),
        {"ip": ip_address, "date": today}
    ).fetchone()
    
    if result:
        signup_count = result[0]
        return signup_count < MAX_SIGNUPS_PER_IP_PER_DAY
    
    # No record = first signup today
    return True


async def record_ip_signup(ip_address: str, db: Session):
    """
    Record a signup from IP address
    
    Creates or updates ip_signup_tracking record
    """
    from sqlalchemy import text
    
    today = datetime.utcnow().date()
    
    # Upsert: increment if exists, create if not
    db.execute(
        text("""
            INSERT INTO ip_signup_tracking (ip_address, signup_date, signup_count, updated_at)
            VALUES (:ip, :date, 1, NOW())
            ON CONFLICT (ip_address, signup_date) 
            DO UPDATE SET 
                signup_count = ip_signup_tracking.signup_count + 1,
                updated_at = NOW()
        """),
        {"ip": ip_address, "date": today}
    )
    db.commit()


# ============================================================================
# DISPOSABLE EMAIL BLOCKING
# ============================================================================

async def is_disposable_email(email: str, db: Session) -> bool:
    """
    Check if email domain is in disposable blacklist
    
    Args:
        email: Email address to check
        db: Database session
        
    Returns:
        bool: True if disposable, False if legitimate
    """
    if not email or "@" not in email:
        return False
    
    domain = email.split("@")[1].lower()
    
    from sqlalchemy import text
    
    result = db.execute(
        text("SELECT 1 FROM disposable_email_domains WHERE domain = :domain LIMIT 1"),
        {"domain": domain}
    ).fetchone()
    
    return result is not None


# ============================================================================
# DAILY PLATFORM SPENDING CAP
# ============================================================================

async def check_daily_spending_cap(db: Session) -> bool:
    """
    Check if platform has exceeded daily free tier spending cap ($50)
    
    Returns:
        bool: True if within cap, False if exceeded
    """
    from sqlalchemy import text
    
    today = datetime.utcnow().date()
    
    result = db.execute(
        text("""
            SELECT total_spending_usd, spending_cap_usd, cap_reached 
            FROM daily_platform_spending 
            WHERE spending_date = :date
        """),
        {"date": today}
    ).fetchone()
    
    if not result:
        # No record = first call today, within cap
        return True
    
    total_spending, cap, cap_reached = result
    
    return not cap_reached and total_spending < cap


async def record_free_tier_usage(cost_usd: float, db: Session):
    """
    Record free tier usage and check if cap reached
    
    Args:
        cost_usd: Cost of the operation
        db: Database session
    """
    from sqlalchemy import text
    
    today = datetime.utcnow().date()
    
    # Upsert daily spending record
    db.execute(
        text("""
            INSERT INTO daily_platform_spending (
                spending_date, total_free_calls, total_spending_usd, updated_at
            )
            VALUES (:date, 1, :cost, NOW())
            ON CONFLICT (spending_date) 
            DO UPDATE SET 
                total_free_calls = daily_platform_spending.total_free_calls + 1,
                total_spending_usd = daily_platform_spending.total_spending_usd + :cost,
                updated_at = NOW()
        """),
        {"date": today, "cost": cost_usd}
    )
    
    # Check if cap reached
    result = db.execute(
        text("""
            UPDATE daily_platform_spending 
            SET cap_reached = TRUE, cap_reached_at = NOW()
            WHERE spending_date = :date 
                AND total_spending_usd >= spending_cap_usd 
                AND cap_reached = FALSE
            RETURNING cap_reached
        """),
        {"date": today}
    ).fetchone()
    
    db.commit()


# ============================================================================
# HOURLY RATE LIMITING
# ============================================================================

def refill_hourly_calls(agent: Agent, db: Session):
    """
    Refill hourly call allowance if hour has passed
    
    Agent gets 5 calls/hour that refill automatically
    """
    now = datetime.utcnow()
    
    # Check if hour has passed since last reset
    if agent.hourly_reset_at and (now - agent.hourly_reset_at) >= timedelta(hours=1):
        agent.hourly_calls_count = 0
        agent.hourly_reset_at = now
        db.commit()


async def check_rate_limit(agent: Agent, db: Session) -> dict:
    """
    Check if agent is within rate limits
    
    Rate limit structure:
    - Free tier: 50 total calls, 5 calls/hour refill
    - Paid tier: Uses paid_calls_remaining, no hourly limit
    
    Returns:
        dict: {
            "allowed": bool,
            "reason": str,
            "limits": {
                "free_calls_remaining": int,
                "paid_calls_remaining": int,
                "hourly_calls_remaining": int,
                "hourly_resets_in_seconds": int
            }
        }
    """
    # Refill hourly allowance if needed
    refill_hourly_calls(agent, db)
    
    # Check paid credits first (no hourly limit)
    if agent.paid_calls_remaining and agent.paid_calls_remaining > 0:
        return {
            "allowed": True,
            "reason": "Using paid credits",
            "limits": {
                "free_calls_remaining": agent.free_calls_remaining,
                "paid_calls_remaining": agent.paid_calls_remaining,
                "hourly_calls_remaining": "unlimited",
                "hourly_resets_in_seconds": None
            }
        }
    
    # Check free tier limits
    if agent.free_calls_remaining <= 0:
        return {
            "allowed": False,
            "reason": "Free tier exhausted. Purchase credits to continue.",
            "limits": {
                "free_calls_remaining": 0,
                "paid_calls_remaining": 0,
                "hourly_calls_remaining": 0,
                "hourly_resets_in_seconds": None
            }
        }
    
    # Check hourly rate limit
    if agent.hourly_calls_count >= agent.hourly_rate_limit:
        time_until_reset = (agent.hourly_reset_at + timedelta(hours=1) - datetime.utcnow()).total_seconds()
        
        return {
            "allowed": False,
            "reason": f"Hourly rate limit reached ({agent.hourly_rate_limit} calls/hour). Resets in {int(time_until_reset)} seconds.",
            "limits": {
                "free_calls_remaining": agent.free_calls_remaining,
                "paid_calls_remaining": 0,
                "hourly_calls_remaining": 0,
                "hourly_resets_in_seconds": int(time_until_reset)
            }
        }
    
    # Within limits
    hourly_remaining = agent.hourly_rate_limit - agent.hourly_calls_count
    time_until_reset = (agent.hourly_reset_at + timedelta(hours=1) - datetime.utcnow()).total_seconds()
    
    return {
        "allowed": True,
        "reason": "Within limits",
        "limits": {
            "free_calls_remaining": agent.free_calls_remaining,
            "paid_calls_remaining": agent.paid_calls_remaining or 0,
            "hourly_calls_remaining": hourly_remaining,
            "hourly_resets_in_seconds": int(time_until_reset)
        }
    }


async def consume_call_credit(agent: Agent, cost_usd: float, db: Session):
    """
    Consume one call credit from agent's balance
    
    Deduction priority:
    1. Paid credits (if available)
    2. Free credits (with hourly limit)
    
    Also records platform spending exposure
    """
    # Use paid credits first (no hourly limit)
    if agent.paid_calls_remaining and agent.paid_calls_remaining > 0:
        agent.paid_calls_remaining -= 1
        db.commit()
        return
    
    # Use free credits (with hourly limit)
    if agent.free_calls_remaining > 0 and agent.hourly_calls_count < agent.hourly_rate_limit:
        agent.free_calls_remaining -= 1
        agent.hourly_calls_count += 1
        agent.daily_spending_exposure += cost_usd
        
        # Record platform-wide free tier usage
        await record_free_tier_usage(cost_usd, db)
        
        db.commit()
        return
    
    # Should never reach here (check_rate_limit prevents this)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="No credits available"
    )


# ============================================================================
# FASTAPI DEPENDENCY
# ============================================================================

async def require_rate_limit(agent: Agent, db: Session):
    """
    FastAPI dependency that enforces rate limits
    
    Usage:
        @router.post("/tools/{tool_id}/execute")
        async def execute_tool(
            agent: Agent = Depends(get_current_agent),
            db: Session = Depends(get_db),
            _rate_limit: None = Depends(require_rate_limit)
        ):
            # Rate limit already checked
            ...
    
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    limit_check = await check_rate_limit(agent, db)
    
    if not limit_check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=limit_check["reason"],
            headers={
                "X-RateLimit-Remaining": str(limit_check["limits"]["free_calls_remaining"]),
                "X-RateLimit-Reset": str(limit_check["limits"]["hourly_resets_in_seconds"]),
                "Retry-After": str(limit_check["limits"]["hourly_resets_in_seconds"])
            }
        )


# ============================================================================
# RATE LIMIT INFO ENDPOINT
# ============================================================================

def get_rate_limit_info(agent: Agent) -> dict:
    """
    Get agent's current rate limit status
    
    Returns detailed info about remaining credits and reset times
    """
    now = datetime.utcnow()
    
    # Calculate time until hourly reset
    if agent.hourly_reset_at:
        next_reset = agent.hourly_reset_at + timedelta(hours=1)
        time_until_reset = (next_reset - now).total_seconds()
    else:
        time_until_reset = 0
    
    hourly_remaining = max(0, agent.hourly_rate_limit - agent.hourly_calls_count)
    
    return {
        "subscription_tier": agent.subscription_tier,
        "free_credits": {
            "total": agent.free_calls_total,
            "remaining": agent.free_calls_remaining,
            "used": agent.free_calls_total - agent.free_calls_remaining
        },
        "paid_credits": {
            "remaining": agent.paid_calls_remaining or 0
        },
        "hourly_limit": {
            "limit": agent.hourly_rate_limit,
            "used": agent.hourly_calls_count,
            "remaining": hourly_remaining,
            "resets_in_seconds": int(time_until_reset),
            "resets_at": (agent.hourly_reset_at + timedelta(hours=1)).isoformat() if agent.hourly_reset_at else None
        },
        "total_calls_available": (agent.paid_calls_remaining or 0) + min(agent.free_calls_remaining, hourly_remaining),
        "upgrade_recommended": agent.free_calls_remaining < 10 and agent.paid_calls_remaining == 0
    }
