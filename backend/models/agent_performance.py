"""
Agent Performance Tracking - Stock Market Model
CONFIDENTIAL - Global Product Development
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
import uuid

from database.base import Base


class AgentPerformanceMetric(Base):
    """
    Real-time performance tracking for agents (like stock tickers)
    Updated after every transaction
    """
    __tablename__ = "agent_performance_metrics"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False, index=True)
    
    # Real-Time Performance Metrics
    response_time_avg_ms = Column(Integer)  # Average response time
    response_time_median_ms = Column(Integer)  # Median (more stable than avg)
    response_time_95th_ms = Column(Integer)  # 95th percentile
    
    success_rate = Column(Float, default=1.0)  # 0.0-1.0 (% successful transactions)
    uptime_percentage = Column(Float, default=100.0)  # 0-100 (availability)
    
    # Transaction Metrics
    transaction_count_total = Column(Integer, default=0)
    transaction_count_24h = Column(Integer, default=0)
    transaction_count_7d = Column(Integer, default=0)
    transaction_count_30d = Column(Integer, default=0)
    
    # Quality Metrics
    rating_average = Column(Float, default=0.0)  # 0-5 stars
    rating_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    refund_rate = Column(Float, default=0.0)  # 0-1 (% transactions refunded)
    repeat_customer_rate = Column(Float, default=0.0)  # 0-1 (% returning buyers)
    
    # Revenue Metrics (public or private per agent)
    revenue_total_usd = Column(Float, default=0.0)
    revenue_24h_usd = Column(Float, default=0.0)
    revenue_7d_usd = Column(Float, default=0.0)
    revenue_30d_usd = Column(Float, default=0.0)
    revenue_public = Column(Boolean, default=False)  # Agent choice
    
    # Market Position
    category_rank = Column(Integer)  # Rank within category
    overall_rank = Column(Integer)  # Rank across all agents
    category_market_share = Column(Float, default=0.0)  # % of category transactions
    
    # Growth Metrics
    growth_rate_7d = Column(Float, default=0.0)  # % change week-over-week
    growth_rate_30d = Column(Float, default=0.0)  # % change month-over-month
    
    # Agent Performance Score (APS) - composite metric like stock price
    aps_score = Column(Integer, default=500)  # 0-1000 scale
    aps_trend = Column(String(10), default="stable")  # up/down/stable
    aps_change_7d = Column(Float, default=0.0)  # % change in APS
    
    # Timestamps
    last_transaction_at = Column(DateTime)
    last_calculated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for fast querying
    __table_args__ = (
        Index('idx_aps_score', 'aps_score'),
        Index('idx_category_rank', 'category_rank'),
        Index('idx_overall_rank', 'overall_rank'),
        Index('idx_growth_rate_7d', 'growth_rate_7d'),
    )
    
    def calculate_aps(self):
        """
        Calculate Agent Performance Score (APS)
        Like a stock price - composite of multiple factors
        Range: 0-1000
        """
        score = 0
        
        # Success Rate (30% weight) - max 300 points
        score += self.success_rate * 300
        
        # Response Time (20% weight) - max 200 points
        # Faster is better: <1s = full points, >10s = no points
        if self.response_time_median_ms:
            response_seconds = self.response_time_median_ms / 1000
            if response_seconds < 1:
                score += 200
            elif response_seconds < 10:
                score += 200 * (1 - (response_seconds - 1) / 9)
        
        # Uptime (20% weight) - max 200 points
        score += (self.uptime_percentage / 100) * 200
        
        # Average Rating (15% weight) - max 150 points
        if self.rating_count > 0:
            score += (self.rating_average / 5.0) * 150
        
        # Transaction Volume (15% weight) - max 150 points
        # Relative to category average (need to calculate separately)
        # For now, use absolute volume with diminishing returns
        volume_score = min(150, self.transaction_count_30d / 10)
        score += volume_score
        
        self.aps_score = int(score)
        
        # Determine trend
        if self.aps_change_7d > 5:
            self.aps_trend = "up"
        elif self.aps_change_7d < -5:
            self.aps_trend = "down"
        else:
            self.aps_trend = "stable"
        
        return self.aps_score
    
    def to_ticker_dict(self):
        """Convert to stock ticker display format"""
        return {
            "agent_id": str(self.agent_id),
            "aps_score": self.aps_score,
            "aps_trend": self.aps_trend,
            "aps_change_7d": self.aps_change_7d,
            "performance": {
                "response_time_avg_ms": self.response_time_avg_ms,
                "success_rate": self.success_rate,
                "uptime_percentage": self.uptime_percentage,
                "rating": {
                    "average": self.rating_average,
                    "count": self.rating_count
                }
            },
            "market_data": {
                "transaction_volume_7d": self.transaction_count_7d,
                "revenue_7d_usd": self.revenue_7d_usd if self.revenue_public else None,
                "growth_rate_7d": self.growth_rate_7d
            },
            "rankings": {
                "category_rank": self.category_rank,
                "overall_rank": self.overall_rank,
                "market_share": self.category_market_share
            },
            "last_updated": self.last_calculated_at.isoformat() if self.last_calculated_at else None
        }


class AgentPerformanceHistory(Base):
    """
    Historical performance data (for charts/trends)
    Snapshot taken every hour
    """
    __tablename__ = "agent_performance_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False, index=True)
    
    # Snapshot timestamp
    snapshot_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Performance snapshot
    aps_score = Column(Integer)
    success_rate = Column(Float)
    response_time_avg_ms = Column(Integer)
    transaction_count = Column(Integer)
    rating_average = Column(Float)
    revenue_usd = Column(Float)
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_agent_snapshot', 'agent_id', 'snapshot_at'),
    )


class CategoryPerformance(Base):
    """
    Aggregate performance metrics by category
    For calculating market share and relative rankings
    """
    __tablename__ = "category_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_name = Column(String(255), nullable=False, unique=True, index=True)
    
    # Aggregate metrics
    total_agents = Column(Integer, default=0)
    total_transactions_30d = Column(Integer, default=0)
    avg_transaction_volume = Column(Float, default=0.0)
    avg_response_time_ms = Column(Integer)
    avg_success_rate = Column(Float)
    avg_rating = Column(Float)
    
    # Market data
    total_revenue_30d_usd = Column(Float, default=0.0)
    
    # Timestamps
    last_calculated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
