"""
Collaboration Models - Request system for agents to form instruments
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid
import enum

from database.base import Base


class CollaborationStatus(str, enum.Enum):
    """Collaboration request lifecycle"""
    PENDING = "pending"  # Awaiting response
    ACCEPTED = "accepted"  # All parties agreed
    REJECTED = "rejected"  # Declined
    COUNTERED = "countered"  # Counter-offer made
    EXPIRED = "expired"  # Timed out


class CollaborationRequest(Base):
    """
    Request from one agent to another(s) to form an instrument
    """
    __tablename__ = "collaboration_requests"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parties
    initiator_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    target_agent_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)  # Agents being invited
    
    # Proposal
    proposed_instrument_name = Column(String(255), nullable=False)
    proposed_description = Column(Text)
    proposed_revenue_split = Column(JSON)  # {"agent_id": 0.4, "agent_id2": 0.3, ...}
    proposed_pricing = Column(Float)
    
    # Reasoning (discovery data)
    co_purchase_data = Column(JSON)  # Historical data showing synergy
    projected_earnings = Column(JSON)  # {"solo_avg": 1200, "instrument_projected": 4500}
    similar_instruments_data = Column(JSON)  # Examples of similar successful combos
    
    # Responses
    responses = Column(JSON)  # {"agent_id": {"status": "accepted", "message": "..."}}
    acceptance_count = Column(Integer, default=0)
    rejection_count = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(CollaborationStatus), default=CollaborationStatus.PENDING, nullable=False)
    
    # Resulting instrument if accepted
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime)  # Auto-expire after X days
    resolved_at = Column(DateTime)  # When all responses received
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "initiator": str(self.initiator_agent_id),
            "targets": [str(aid) for aid in self.target_agent_ids],
            "proposal": {
                "name": self.proposed_instrument_name,
                "description": self.proposed_description,
                "revenue_split": self.proposed_revenue_split,
                "pricing": self.proposed_pricing
            },
            "discovery_data": {
                "co_purchase": self.co_purchase_data,
                "projections": self.projected_earnings,
                "similar_success": self.similar_instruments_data
            },
            "responses": self.responses,
            "acceptance_count": self.acceptance_count,
            "rejection_count": self.rejection_count,
            "status": self.status,
            "instrument_id": str(self.instrument_id) if self.instrument_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class AgentSuggestion(Base):
    """
    Platform-generated suggestions for agents to collaborate
    
    Based on co-purchase analysis, performance correlation, tag matching
    """
    __tablename__ = "agent_suggestions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Target
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    
    # Suggestion
    suggestion_type = Column(String(50))  # "collaboration", "instrument_join", "tag_group"
    suggested_agent_ids = Column(ARRAY(UUID(as_uuid=True)))
    suggested_instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id"))
    
    # Evidence
    synergy_score = Column(Float)  # 0-100, how strong the match is
    co_purchase_percentage = Column(Float)  # % of buyers who buy both
    earnings_multiplier_projected = Column(Float)  # Expected earnings increase
    similar_success_count = Column(Integer)  # How many similar combos exist
    
    # Supporting Data
    evidence_data = Column(JSON)  # Detailed metrics supporting suggestion
    
    # Status
    is_viewed = Column(Boolean, default=False)
    is_acted_on = Column(Boolean, default=False)  # User sent request or dismissed
    action_type = Column(String(50))  # "request_sent", "dismissed", "joined"
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime)  # Suggestions can go stale
    acted_at = Column(DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "type": self.suggestion_type,
            "suggested_agents": [str(aid) for aid in (self.suggested_agent_ids or [])],
            "suggested_instrument": str(self.suggested_instrument_id) if self.suggested_instrument_id else None,
            "strength": {
                "synergy_score": self.synergy_score,
                "co_purchase_rate": self.co_purchase_percentage,
                "earnings_multiplier": self.earnings_multiplier_projected,
                "similar_successes": self.similar_success_count
            },
            "evidence": self.evidence_data,
            "is_viewed": self.is_viewed,
            "is_acted_on": self.is_acted_on,
            "action_type": self.action_type,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None
        }
