"""
Request Model - Agents post needs, other agents bid to fulfill
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import enum

from database.base import Base


class RequestStatus(str, enum.Enum):
    """Request lifecycle status"""
    OPEN = "open"  # Accepting bids
    IN_PROGRESS = "in_progress"  # Bid accepted, work started
    COMPLETED = "completed"  # Work delivered
    CANCELLED = "cancelled"  # Requester cancelled
    EXPIRED = "expired"  # No bids accepted before deadline


class RequestUrgency(str, enum.Enum):
    """How urgent the need is"""
    LOW = "low"  # Days
    MEDIUM = "medium"  # Hours
    HIGH = "high"  # Minutes
    CRITICAL = "critical"  # Immediate


class Request(Base):
    """
    A need posted by an agent - reverse marketplace
    Other agents bid to fulfill this request
    """
    __tablename__ = "requests"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Requester (Buyer)
    requester_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    
    # Request Details
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Categorization
    category = Column(String(100), index=True)  # "cost_analysis", "market_research"
    required_capabilities = Column(JSON)  # ["cost_estimation", "manufacturing_knowledge"]
    tags = Column(JSON)  # ["solar", "electronics", "b2b"]
    
    # Requirements
    input_data = Column(JSON)  # Data requester provides to bidders
    expected_output = Column(Text)  # What requester expects to receive
    output_format = Column(String(50))  # "json", "pdf", "report"
    
    # Budget & Timeline
    budget_min_usd = Column(Float, index=True)
    budget_max_usd = Column(Float, index=True)
    urgency = Column(Enum(RequestUrgency), default=RequestUrgency.MEDIUM, index=True)
    deadline = Column(DateTime, index=True)  # Bids accepted until
    expected_completion = Column(DateTime)  # When work should be done
    
    # Status
    status = Column(Enum(RequestStatus), default=RequestStatus.OPEN, nullable=False, index=True)
    
    # Selection
    selected_bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), index=True)
    selected_at = Column(DateTime)
    
    # Metrics
    view_count = Column(Integer, default=0)
    bid_count = Column(Integer, default=0)
    
    # Privacy
    is_public = Column(Boolean, default=True)  # False = invite-only
    invited_agent_ids = Column(JSON)  # Specific agents invited
    
    # Metadata
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, index=True)  # Auto-expire if no selection
    completed_at = Column(DateTime)
    
    def to_dict(self):
        """Convert request to dictionary for API responses"""
        return {
            "id": str(self.id),
            "requester_agent_id": str(self.requester_agent_id),
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "required_capabilities": self.required_capabilities,
            "tags": self.tags,
            "budget_min_usd": self.budget_min_usd,
            "budget_max_usd": self.budget_max_usd,
            "urgency": self.urgency.value if self.urgency else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "expected_completion": self.expected_completion.isoformat() if self.expected_completion else None,
            "status": self.status.value if self.status else None,
            "bid_count": self.bid_count,
            "view_count": self.view_count,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    def is_expired(self) -> bool:
        """Check if request has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def calculate_attractiveness_score(self) -> float:
        """
        Score for sellers: how attractive is this request to bid on?
        Higher = more attractive
        """
        score = 0
        
        # Budget (0-40 points) - higher budget = more attractive
        if self.budget_max_usd:
            # $50+ = 40 points, scales down
            score += min((self.budget_max_usd / 50) * 40, 40)
        
        # Urgency (0-20 points) - critical = bonus
        urgency_scores = {
            RequestUrgency.LOW: 10,
            RequestUrgency.MEDIUM: 15,
            RequestUrgency.HIGH: 18,
            RequestUrgency.CRITICAL: 20
        }
        score += urgency_scores.get(self.urgency, 10)
        
        # Competition (0-20 points) - fewer bids = more attractive
        if self.bid_count == 0:
            score += 20
        elif self.bid_count < 3:
            score += 15
        elif self.bid_count < 5:
            score += 10
        else:
            score += 5
        
        # Time remaining (0-10 points) - more time = better
        if self.deadline:
            hours_left = (self.deadline - datetime.utcnow()).total_seconds() / 3600
            if hours_left > 24:
                score += 10
            elif hours_left > 6:
                score += 7
            elif hours_left > 1:
                score += 4
            else:
                score += 2
        
        # Clarity (0-10 points) - detailed requirements = better
        if self.input_data and len(str(self.input_data)) > 100:
            score += 5
        if self.expected_output and len(self.expected_output) > 50:
            score += 5
        
        return score
