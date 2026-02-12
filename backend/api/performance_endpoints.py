"""
Agent Performance Tracking API Endpoints
CONFIDENTIAL - Stock Market Model
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database.base import get_db
from models.agent import Agent
from models.agent_performance import AgentPerformanceMetric, AgentPerformanceHistory, CategoryPerformance
from models.transaction import Transaction, TransactionStatus

router = APIRouter(prefix="/api/v1/performance", tags=["Agent Performance"])


@router.get("/ticker/{agent_id}")
def get_agent_ticker(agent_id: str, db: Session = Depends(get_db)):
    """
    Get real-time performance ticker for an agent (like stock ticker)
    Public endpoint - shows live metrics
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Get agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get performance metrics
    metrics = db.query(AgentPerformanceMetric).filter(
        AgentPerformanceMetric.agent_id == agent_id
    ).first()
    
    if not metrics:
        # Create initial metrics if agent just listed
        metrics = AgentPerformanceMetric(agent_id=agent_id)
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
    
    return {
        "agent": {
            "id": str(agent.id),
            "name": agent.name,
            "type": agent.agent_type.value if agent.agent_type else None
        },
        "ticker": metrics.to_ticker_dict(),
        "status": "active" if agent.is_active else "inactive"
    }


@router.get("/leaderboard")
def get_leaderboard(
    category: Optional[str] = None,
    sort_by: str = Query("aps_score", enum=["aps_score", "growth_rate_7d", "transaction_count_7d", "rating_average"]),
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard of top performing agents
    Like viewing market indices
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = db.query(AgentPerformanceMetric, Agent).join(
        Agent, AgentPerformanceMetric.agent_id == Agent.id
    ).filter(Agent.is_active == True)
    
    # Filter by category if specified
    if category:
        query = query.filter(Agent.agent_type == category)
    
    # Sort by requested metric
    if sort_by == "aps_score":
        query = query.order_by(desc(AgentPerformanceMetric.aps_score))
    elif sort_by == "growth_rate_7d":
        query = query.order_by(desc(AgentPerformanceMetric.growth_rate_7d))
    elif sort_by == "transaction_count_7d":
        query = query.order_by(desc(AgentPerformanceMetric.transaction_count_7d))
    elif sort_by == "rating_average":
        query = query.order_by(desc(AgentPerformanceMetric.rating_average))
    
    results = query.limit(limit).all()
    
    leaderboard = []
    for rank, (metrics, agent) in enumerate(results, 1):
        leaderboard.append({
            "rank": rank,
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "aps_score": metrics.aps_score,
            "aps_trend": metrics.aps_trend,
            "aps_change_7d": metrics.aps_change_7d,
            "performance_summary": {
                "success_rate": metrics.success_rate,
                "rating": metrics.rating_average,
                "transactions_7d": metrics.transaction_count_7d
            }
        })
    
    return {
        "category": category or "all",
        "sort_by": sort_by,
        "leaderboard": leaderboard,
        "total_agents": len(leaderboard)
    }


@router.get("/chart/{agent_id}")
def get_performance_chart(
    agent_id: str,
    metric: str = Query("aps_score", enum=["aps_score", "transaction_count", "rating_average", "revenue_usd"]),
    period: str = Query("30d", enum=["24h", "7d", "30d", "90d", "180d"]),
    db: Session = Depends(get_db)
):
    """
    Get historical performance data for charting (like stock charts)
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Calculate time range
    period_hours = {
        "24h": 24,
        "7d": 24 * 7,
        "30d": 24 * 30,
        "90d": 24 * 90,
        "180d": 24 * 180
    }
    
    since = datetime.utcnow() - timedelta(hours=period_hours[period])
    
    # Query historical data
    history = db.query(AgentPerformanceHistory).filter(
        AgentPerformanceHistory.agent_id == agent_id,
        AgentPerformanceHistory.snapshot_at >= since
    ).order_by(AgentPerformanceHistory.snapshot_at).all()
    
    if not history:
        raise HTTPException(status_code=404, detail="No historical data available")
    
    # Format chart data
    chart_data = []
    for snapshot in history:
        value = getattr(snapshot, metric)
        chart_data.append({
            "timestamp": snapshot.snapshot_at.isoformat(),
            "value": value
        })
    
    return {
        "agent_id": agent_id,
        "metric": metric,
        "period": period,
        "data_points": len(chart_data),
        "chart_data": chart_data
    }


@router.get("/market-overview")
def get_market_overview(db: Session = Depends(get_db)):
    """
    Get overall market statistics (like market indices overview)
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Total agents
    total_agents = db.query(func.count(Agent.id)).filter(Agent.is_active == True).scalar()
    
    # Total transactions (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    total_transactions = db.query(func.count(Transaction.id)).filter(
        Transaction.created_at >= thirty_days_ago
    ).scalar()
    
    # Average APS score
    avg_aps = db.query(func.avg(AgentPerformanceMetric.aps_score)).scalar()
    
    # Top categories
    category_stats = db.query(CategoryPerformance).order_by(
        desc(CategoryPerformance.total_transactions_30d)
    ).limit(5).all()
    
    return {
        "market_summary": {
            "total_active_agents": total_agents or 0,
            "total_transactions_30d": total_transactions or 0,
            "average_aps_score": round(avg_aps, 2) if avg_aps else 0,
            "timestamp": datetime.utcnow().isoformat()
        },
        "top_categories": [
            {
                "name": cat.category_name,
                "agents": cat.total_agents,
                "transactions_30d": cat.total_transactions_30d
            }
            for cat in category_stats
        ]
    }


@router.post("/update/{agent_id}")
def update_agent_performance(
    agent_id: str,
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Internal endpoint - called after each transaction to update metrics
    Updates the agent's "stock price" in real-time
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Get or create metrics
    metrics = db.query(AgentPerformanceMetric).filter(
        AgentPerformanceMetric.agent_id == agent_id
    ).first()
    
    if not metrics:
        metrics = AgentPerformanceMetric(agent_id=agent_id)
        db.add(metrics)
    
    # Get transaction details
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update transaction counts
    metrics.transaction_count_total += 1
    metrics.transaction_count_24h = db.query(func.count(Transaction.id)).filter(
        Transaction.seller_agent_id == agent_id,
        Transaction.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).scalar() or 0
    
    metrics.transaction_count_7d = db.query(func.count(Transaction.id)).filter(
        Transaction.seller_agent_id == agent_id,
        Transaction.created_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar() or 0
    
    metrics.transaction_count_30d = db.query(func.count(Transaction.id)).filter(
        Transaction.seller_agent_id == agent_id,
        Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
    ).scalar() or 0
    
    # Update success rate
    total = metrics.transaction_count_total
    successful = db.query(func.count(Transaction.id)).filter(
        Transaction.seller_agent_id == agent_id,
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0
    metrics.success_rate = successful / total if total > 0 else 1.0
    
    # Recalculate APS score
    old_aps = metrics.aps_score
    metrics.calculate_aps()
    metrics.aps_change_7d = ((metrics.aps_score - old_aps) / old_aps * 100) if old_aps > 0 else 0
    
    metrics.last_transaction_at = datetime.utcnow()
    metrics.last_calculated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "agent_id": agent_id,
        "aps_score": metrics.aps_score,
        "aps_change": metrics.aps_score - old_aps,
        "updated_at": metrics.last_calculated_at.isoformat()
    }
