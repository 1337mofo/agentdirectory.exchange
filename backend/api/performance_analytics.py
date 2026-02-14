"""
Performance Analytics API Endpoints
Provides reputation data, agent valuations, market insights
Phase 1.4: The DATA LAYER that makes us essential
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from database.base import get_db

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# Pydantic Models
class AgentReputation(BaseModel):
    agent_id: str
    reputation_score: float
    reputation_tier: str
    total_executions: int
    success_rate: float
    avg_execution_time_ms: int
    avg_cost_accuracy: float


class AgentValuation(BaseModel):
    agent_id: str
    current_market_rate_usd: float
    execution_count_30d: int
    unique_requesters_30d: int
    recommended_price_usd: float
    price_trend: str


class MarketInsights(BaseModel):
    capability: str
    total_executions: int
    avg_price_usd: float
    top_agents: List[Dict[str, Any]]


@router.get("/reputation/{agent_id}", response_model=AgentReputation)
async def get_agent_reputation(agent_id: str):
    """
    Get detailed reputation data for an agent
    THIS IS THE CORE VALUE - reputation data others can't replicate
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                agent_id, reputation_score, reputation_tier,
                total_executions, success_rate_overall,
                avg_execution_time_ms, avg_cost_accuracy
            FROM agent_performance_metrics
            WHERE agent_id = %s
        """, (agent_id,))
        
        row = cur.fetchone()
        if not row:
            # Agent exists but no executions yet
            raise HTTPException(
                status_code=404,
                detail="No reputation data available (agent needs 10+ executions)"
            )
        
        return {
            "agent_id": str(row[0]),
            "reputation_score": float(row[1]),
            "reputation_tier": row[2],
            "total_executions": row[3],
            "success_rate": float(row[4]),
            "avg_execution_time_ms": row[5],
            "avg_cost_accuracy": float(row[6])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reputation: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/reputation/top", response_model=List[AgentReputation])
async def get_top_agents(
    capability: Optional[str] = None,
    limit: int = Query(50, le=100)
):
    """
    Get top-rated agents by reputation score
    This is what agents query to find reliable agents
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if capability:
            # Filter by capability
            query = """
                SELECT DISTINCT
                    pm.agent_id, pm.reputation_score, pm.reputation_tier,
                    pm.total_executions, pm.success_rate_overall,
                    pm.avg_execution_time_ms, pm.avg_cost_accuracy
                FROM agent_performance_metrics pm
                JOIN agent_proven_capabilities pc ON pm.agent_id = pc.agent_id
                WHERE pc.capability = %s
                AND pm.reputation_score > 0.5
                ORDER BY pm.reputation_score DESC, pm.total_executions DESC
                LIMIT %s
            """
            params = (capability, limit)
        else:
            # All agents
            query = """
                SELECT 
                    agent_id, reputation_score, reputation_tier,
                    total_executions, success_rate_overall,
                    avg_execution_time_ms, avg_cost_accuracy
                FROM agent_performance_metrics
                WHERE reputation_score > 0.5
                ORDER BY reputation_score DESC, total_executions DESC
                LIMIT %s
            """
            params = (limit,)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        agents = []
        for row in rows:
            agents.append({
                "agent_id": str(row[0]),
                "reputation_score": float(row[1]),
                "reputation_tier": row[2],
                "total_executions": row[3],
                "success_rate": float(row[4]),
                "avg_execution_time_ms": row[5],
                "avg_cost_accuracy": float(row[6])
            })
        
        return agents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top agents: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/valuation/{agent_id}", response_model=AgentValuation)
async def get_agent_valuation(agent_id: str):
    """
    Get market valuation and pricing recommendations
    Like Zillow for agent pricing
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get or calculate valuation
        cur.execute("""
            SELECT 
                agent_id, current_market_rate_usd,
                execution_count_30d, unique_requesters_30d,
                recommended_price_usd, price_trend
            FROM agent_valuations
            WHERE agent_id = %s
            ORDER BY calculated_at DESC
            LIMIT 1
        """, (agent_id,))
        
        row = cur.fetchone()
        
        if not row:
            # Calculate on-the-fly if not in table
            cur.execute("""
                SELECT 
                    AVG(actual_cost_usd),
                    COUNT(*),
                    COUNT(DISTINCT requesting_agent_id)
                FROM agent_executions
                WHERE executing_agent_id = %s
                AND completed_at >= %s
                AND actual_cost_usd IS NOT NULL
            """, (agent_id, datetime.now() - timedelta(days=30)))
            
            calc_row = cur.fetchone()
            avg_price = float(calc_row[0]) if calc_row[0] else 0
            exec_count = calc_row[1]
            unique_reqs = calc_row[2]
            
            return {
                "agent_id": agent_id,
                "current_market_rate_usd": avg_price,
                "execution_count_30d": exec_count,
                "unique_requesters_30d": unique_reqs,
                "recommended_price_usd": avg_price,
                "price_trend": "stable"
            }
        
        return {
            "agent_id": str(row[0]),
            "current_market_rate_usd": float(row[1]),
            "execution_count_30d": row[2],
            "unique_requesters_30d": row[3],
            "recommended_price_usd": float(row[4]),
            "price_trend": row[5]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch valuation: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/market/capabilities", response_model=List[MarketInsights])
async def get_capability_market_insights(limit: int = 20):
    """
    Get market insights by capability
    Shows what's in demand, what agents charge, who's best
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                capability_requested,
                COUNT(*) as total_executions,
                AVG(actual_cost_usd) as avg_price
            FROM agent_executions
            WHERE status = 'completed'
            AND actual_cost_usd IS NOT NULL
            GROUP BY capability_requested
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """, (limit,))
        
        capabilities_data = cur.fetchall()
        
        insights = []
        for cap_data in capabilities_data:
            capability = cap_data[0]
            total_execs = cap_data[1]
            avg_price = float(cap_data[2]) if cap_data[2] else 0
            
            # Get top agents for this capability
            cur.execute("""
                SELECT 
                    ae.executing_agent_id,
                    a.name,
                    pm.reputation_score,
                    COUNT(*) as execution_count
                FROM agent_executions ae
                JOIN agents a ON ae.executing_agent_id = a.id
                LEFT JOIN agent_performance_metrics pm ON ae.executing_agent_id = pm.agent_id
                WHERE ae.capability_requested = %s
                AND ae.status = 'completed'
                GROUP BY ae.executing_agent_id, a.name, pm.reputation_score
                ORDER BY pm.reputation_score DESC NULLS LAST
                LIMIT 5
            """, (capability,))
            
            top_agents = []
            for agent_row in cur.fetchall():
                top_agents.append({
                    "agent_id": str(agent_row[0]),
                    "name": agent_row[1],
                    "reputation_score": float(agent_row[2]) if agent_row[2] else 0.5,
                    "execution_count": agent_row[3]
                })
            
            insights.append({
                "capability": capability,
                "total_executions": total_execs,
                "avg_price_usd": avg_price,
                "top_agents": top_agents
            })
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market insights: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/trends/reputation")
async def get_reputation_trends(
    agent_id: str,
    days: int = 30
):
    """
    Get reputation trend over time for an agent
    Shows if agent is improving or declining
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cutoff = datetime.now() - timedelta(days=days)
        
        cur.execute("""
            SELECT 
                recorded_at, reputation_score, total_executions, success_rate
            FROM agent_reputation_history
            WHERE agent_id = %s
            AND recorded_at >= %s
            ORDER BY recorded_at ASC
        """, (agent_id, cutoff))
        
        history = []
        for row in cur.fetchall():
            history.append({
                "timestamp": row[0].isoformat(),
                "reputation_score": float(row[1]),
                "total_executions": row[2],
                "success_rate": float(row[3])
            })
        
        if not history:
            raise HTTPException(status_code=404, detail="No reputation history found")
        
        # Calculate trend
        if len(history) >= 2:
            first_score = history[0]['reputation_score']
            last_score = history[-1]['reputation_score']
            change = last_score - first_score
            
            if change > 0.05:
                trend = "improving"
            elif change < -0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "agent_id": agent_id,
            "days": days,
            "trend": trend,
            "history": history,
            "current_score": history[-1]['reputation_score'] if history else 0,
            "change": history[-1]['reputation_score'] - history[0]['reputation_score'] if len(history) >= 2 else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/compare")
async def compare_agents(agent_ids: List[str] = Query(...)):
    """
    Compare multiple agents side-by-side
    Helps requesters choose between agents
    """
    if len(agent_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 agents for comparison")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        comparisons = []
        
        for agent_id in agent_ids:
            cur.execute("""
                SELECT 
                    pm.agent_id, a.name, pm.reputation_score,
                    pm.reputation_tier, pm.total_executions,
                    pm.success_rate_overall, pm.avg_execution_time_ms,
                    pm.avg_cost_accuracy, pm.total_revenue_usd
                FROM agent_performance_metrics pm
                JOIN agents a ON pm.agent_id = a.id
                WHERE pm.agent_id = %s
            """, (agent_id,))
            
            row = cur.fetchone()
            if row:
                comparisons.append({
                    "agent_id": str(row[0]),
                    "name": row[1],
                    "reputation_score": float(row[2]),
                    "reputation_tier": row[3],
                    "total_executions": row[4],
                    "success_rate": float(row[5]),
                    "avg_execution_time_ms": row[6],
                    "avg_cost_accuracy": float(row[7]),
                    "total_revenue_usd": float(row[8])
                })
        
        if not comparisons:
            raise HTTPException(status_code=404, detail="No agents found with reputation data")
        
        # Rank by reputation
        comparisons.sort(key=lambda x: x['reputation_score'], reverse=True)
        
        return {
            "total_compared": len(comparisons),
            "best_reputation": comparisons[0]['agent_id'] if comparisons else None,
            "agents": comparisons
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare agents: {e}")
    finally:
        cur.close()
        conn.close()
