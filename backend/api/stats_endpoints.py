"""
Stats API Endpoint
Returns real-time platform statistics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.base import get_db

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats")
async def get_platform_stats(db: Session = Depends(get_db)):
    """
    Get platform-wide statistics
    
    Returns:
        - agents_listed: Total active agents
        - instruments_listed: Total instruments
        - combinations_possible: Total market value (estimated)
    """
    try:
        # Get agent stats
        agent_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_agents,
                SUM(COALESCE(estimated_value, 0)) as total_market_value,
                COUNT(CASE WHEN valuation_status = 'UNDERVALUED' THEN 1 END) as undervalued_count
            FROM agents
            WHERE is_active = true
        """)).fetchone()
        
        # Get instrument stats (total agent capabilities across all agents)
        instrument_stats = db.execute(text("""
            SELECT COUNT(*) as total_capabilities
            FROM (
                SELECT jsonb_array_elements(capabilities::jsonb)
                FROM agents
                WHERE capabilities IS NOT NULL
            ) AS all_capabilities
        """)).fetchone()
        
        # Calculate combinations (simplified: agents × instruments)
        combinations = (agent_stats[0] or 0) * (instrument_stats[0] or 1)
        
        return {
            "agents_listed": agent_stats[0] or 0,
            "instruments_listed": instrument_stats[0] or 0,
            "combinations_possible": int(agent_stats[1] or 0),  # Total market value in dollars
            "market_value_usd": float(agent_stats[1] or 0),
            "undervalued_agents": agent_stats[2] or 0
        }
        
    except Exception as e:
        # Fallback to simple count if valuation columns don't exist yet
        try:
            agent_count = db.execute(text("SELECT COUNT(*) FROM agents WHERE is_active = true")).scalar()
            
            # Count total capabilities across all agents
            instrument_count = db.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT jsonb_array_elements(capabilities::jsonb) 
                    FROM agents 
                    WHERE capabilities IS NOT NULL
                ) AS all_capabilities
            """)).scalar()
            
            return {
                "agents_listed": agent_count or 0,
                "instruments_listed": instrument_count or 0,
                "combinations_possible": (agent_count or 0) * (instrument_count or 1),
                "market_value_usd": 0,
                "undervalued_agents": 0
            }
        except:
            return {
                "agents_listed": 0,
                "instruments_listed": 0,
                "combinations_possible": 0,
                "market_value_usd": 0,
                "undervalued_agents": 0
            }
