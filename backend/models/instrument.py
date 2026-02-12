"""
Instrument Model - Collaborative agent groups
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database.base import Base


class InstrumentStatus(str, enum.Enum):
    """Instrument lifecycle status"""
    FORMING = "forming"  # Members joining, not yet active
    ACTIVE = "active"  # Operating and taking transactions
    PAUSED = "paused"  # Temporarily not accepting work
    DISSOLVED = "dissolved"  # Instrument disbanded


class RevenueSplitModel(str, enum.Enum):
    """How revenue is divided among members"""
    EQUAL = "equal"  # Split equally among all members
    USAGE_BASED = "usage_based"  # Based on actual usage metrics
    CUSTOM = "custom"  # Custom percentages defined
    CONTRIBUTION = "contribution"  # Based on contribution to outcome


class Instrument(Base):
    """
    Collaborative group of agents working together
    
    Multiple agents combine capabilities to offer higher-value service
    """
    __tablename__ = "instruments"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Formation
    created_by_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    formation_type = Column(String(50))  # "request", "tag_based", "market_discovered"
    common_tags = Column(ARRAY(String))  # Tags that members share (e.g., ["sibysi"])
    
    # Members
    member_agent_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)  # List of agent UUIDs
    member_count = Column(Integer, default=0)
    
    # Revenue Model
    revenue_split_model = Column(Enum(RevenueSplitModel), default=RevenueSplitModel.EQUAL)
    revenue_split_config = Column(JSON)  # {"agent_id": 0.33, "agent_id2": 0.33, ...}
    
    # Pricing
    base_price_usd = Column(Float)  # Price as instrument
    pricing_vs_solo_multiplier = Column(Float)  # e.g., 0.9 = 10% discount vs buying solo
    
    # Performance
    total_revenue_usd = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Combined success rate
    avg_response_time_seconds = Column(Integer)
    rating_avg = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Discovery Metrics
    co_purchase_strength = Column(Float, default=0.0)  # How often members bought together solo
    value_multiplier = Column(Float, default=1.0)  # Revenue as instrument / sum of solo
    synergy_score = Column(Float, default=0.0)  # 0-100, how well agents work together
    
    # Status
    status = Column(Enum(InstrumentStatus), default=InstrumentStatus.FORMING, nullable=False)
    is_accepting_members = Column(Boolean, default=False)  # Open for new members to join
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime)  # When it went active
    dissolved_at = Column(DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_by": str(self.created_by_agent_id),
            "formation_type": self.formation_type,
            "common_tags": self.common_tags,
            "member_agent_ids": [str(aid) for aid in self.member_agent_ids],
            "member_count": self.member_count,
            "revenue_split_model": self.revenue_split_model,
            "revenue_split_config": self.revenue_split_config,
            "base_price_usd": self.base_price_usd,
            "pricing_vs_solo_multiplier": self.pricing_vs_solo_multiplier,
            "performance": {
                "total_revenue": self.total_revenue_usd,
                "transactions": self.transaction_count,
                "success_rate": self.success_rate,
                "avg_response_time": self.avg_response_time_seconds,
                "rating": self.rating_avg,
                "rating_count": self.rating_count
            },
            "discovery": {
                "co_purchase_strength": self.co_purchase_strength,
                "value_multiplier": self.value_multiplier,
                "synergy_score": self.synergy_score
            },
            "status": self.status,
            "is_accepting_members": self.is_accepting_members,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None
        }
