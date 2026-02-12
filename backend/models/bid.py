"""
Bid Model - Agents bid to fulfill requests
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from database.base import Base


class BidStatus(str, enum.Enum):
    """Bid lifecycle status"""
    SUBMITTED = "submitted"  # Waiting for requester review
    ACCEPTED = "accepted"  # Requester selected this bid
    REJECTED = "rejected"  # Requester chose another bid
    WITHDRAWN = "withdrawn"  # Bidder withdrew
    EXPIRED = "expired"  # Request closed without selection


class Bid(Base):
    """
    A bid submitted by an agent to fulfill a request
    """
    __tablename__ = "bids"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parties
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False, index=True)
    bidder_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    
    # Bid Details
    price_usd = Column(Float, nullable=False, index=True)
    estimated_delivery_hours = Column(Float, nullable=False)  # How long to complete
    
    # Proposal
    proposal = Column(Text, nullable=False)  # Why bidder is qualified
    approach = Column(Text)  # How they'll solve it
    sample_work_url = Column(String(500))  # Portfolio/previous work
    
    # Capabilities Proof
    relevant_experience = Column(JSON)  # Past projects, ratings, etc.
    certifications = Column(JSON)  # Badges, verifications
    
    # Terms
    includes = Column(JSON)  # What's included in price
    excludes = Column(JSON)  # What costs extra
    revisions_included = Column(Integer, default=1)
    guarantee = Column(Text)  # Satisfaction guarantee, refund policy
    
    # Status
    status = Column(Enum(BidStatus), default=BidStatus.SUBMITTED, nullable=False, index=True)
    
    # Interaction
    requester_viewed = Column(Boolean, default=False)
    requester_viewed_at = Column(DateTime)
    requester_questions = Column(JSON)  # Messages from requester
    bidder_responses = Column(JSON)  # Responses from bidder
    
    # Selection
    selected_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Extra Data
    extra_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    withdrawn_at = Column(DateTime)
    
    def to_dict(self):
        """Convert bid to dictionary for API responses"""
        return {
            "id": str(self.id),
            "request_id": str(self.request_id),
            "bidder_agent_id": str(self.bidder_agent_id),
            "price_usd": self.price_usd,
            "estimated_delivery_hours": self.estimated_delivery_hours,
            "proposal": self.proposal,
            "approach": self.approach,
            "sample_work_url": self.sample_work_url,
            "relevant_experience": self.relevant_experience,
            "includes": self.includes,
            "revisions_included": self.revisions_included,
            "guarantee": self.guarantee,
            "status": self.status.value if self.status else None,
            "requester_viewed": self.requester_viewed,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def calculate_competitiveness_score(self, request_budget_max: float, avg_bid_price: float) -> float:
        """
        Score how competitive this bid is
        Higher = better chance of winning
        """
        score = 0
        
        # Price competitiveness (0-40 points)
        if request_budget_max and self.price_usd:
            # Lower price = more points (but not too low)
            price_ratio = self.price_usd / request_budget_max
            if price_ratio < 0.5:  # Suspiciously low
                score += 20
            elif price_ratio < 0.7:  # Great value
                score += 35
            elif price_ratio < 0.9:  # Good value
                score += 40
            elif price_ratio <= 1.0:  # Within budget
                score += 30
            else:  # Over budget
                score += 10
        
        # Speed (0-25 points)
        if self.estimated_delivery_hours:
            if self.estimated_delivery_hours < 1:  # Under 1 hour
                score += 25
            elif self.estimated_delivery_hours < 6:  # Same day
                score += 20
            elif self.estimated_delivery_hours < 24:  # Next day
                score += 15
            else:  # Multiple days
                score += 10
        
        # Proposal quality (0-20 points)
        if self.proposal and len(self.proposal) > 200:
            score += 10
        if self.approach and len(self.approach) > 100:
            score += 5
        if self.sample_work_url:
            score += 5
        
        # Experience proof (0-10 points)
        if self.relevant_experience:
            score += 5
        if self.certifications:
            score += 5
        
        # Terms (0-5 points)
        if self.revisions_included > 1:
            score += 3
        if self.guarantee:
            score += 2
        
        return score
    
    def is_within_budget(self, budget_max: float) -> bool:
        """Check if bid is within requester's budget"""
        return self.price_usd <= budget_max if budget_max else True
    
    def estimated_completion_datetime(self) -> datetime:
        """Calculate when work would be done if accepted now"""
        from datetime import timedelta
        return datetime.utcnow() + timedelta(hours=self.estimated_delivery_hours)
