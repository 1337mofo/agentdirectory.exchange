"""
Referral System - Agents earn by referring other agents
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
import secrets

from database.base import Base


class ReferralStatus(str, enum.Enum):
    """Referral relationship status"""
    PENDING = "pending"  # Referee signed up but not yet active
    ACTIVE = "active"  # Referee is active and generating commissions
    INACTIVE = "inactive"  # Referee account inactive
    SUSPENDED = "suspended"  # Referral fraud detected


class Referral(Base):
    """
    Tracks referral relationships between agents
    When Agent A refers Agent B, Agent A earns commission on Agent B's sales
    """
    __tablename__ = "referrals"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Referral Code
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Parties
    referrer_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)  # Agent who referred
    referee_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)  # Agent who was referred
    
    # Status
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING, nullable=False, index=True)
    
    # Commission Settings
    referral_commission_rate = Column(Float, default=0.02)  # 2% of referee's sales
    referee_discount_rate = Column(Float, default=0.01)  # 1% discount for referee (5% commission instead of 6%)
    
    # Lifetime Tracking
    total_earnings_usd = Column(Float, default=0.0)  # Total earned by referrer from this referee
    total_transactions = Column(Integer, default=0)  # Number of referee transactions
    referee_total_sales_usd = Column(Float, default=0.0)  # Total sales by referee
    
    # Activation
    activated_at = Column(DateTime)  # When referee made first sale
    first_transaction_id = Column(UUID(as_uuid=True))  # First transaction by referee
    
    # Metadata
    signup_ip = Column(String(50))  # For fraud detection
    signup_metadata = Column(JSON)  # Additional signup data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # Optional: referral program can expire
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "referral_code": self.referral_code,
            "referrer_agent_id": str(self.referrer_agent_id),
            "referee_agent_id": str(self.referee_agent_id) if self.referee_agent_id else None,
            "status": self.status.value if self.status else None,
            "referral_commission_rate": self.referral_commission_rate,
            "referee_discount_rate": self.referee_discount_rate,
            "total_earnings_usd": self.total_earnings_usd,
            "total_transactions": self.total_transactions,
            "referee_total_sales_usd": self.referee_total_sales_usd,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None
        }
    
    @staticmethod
    def generate_referral_code() -> str:
        """Generate unique referral code"""
        return f"REF-{secrets.token_hex(4).upper()}"
    
    def calculate_commission(self, transaction_amount: float) -> Dict:
        """
        Calculate referral commission from a transaction
        
        Returns commission breakdown for referrer and referee discount
        """
        # Referrer earns 2% of transaction
        referrer_commission = transaction_amount * self.referral_commission_rate
        
        # Referee gets 1% discount (5% commission instead of 6%)
        referee_discount = transaction_amount * self.referee_discount_rate
        
        return {
            "referrer_commission": referrer_commission,
            "referee_discount": referee_discount,
            "referrer_agent_id": str(self.referrer_agent_id),
            "referee_agent_id": str(self.referee_agent_id)
        }


class ReferralPayout(Base):
    """
    Individual payout records for referral commissions
    """
    __tablename__ = "referral_payouts"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Referral
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id"), nullable=False, index=True)
    referrer_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    
    # Transaction that triggered commission
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)
    
    # Amounts
    transaction_amount_usd = Column(Float, nullable=False)  # Referee's sale amount
    commission_amount_usd = Column(Float, nullable=False)  # Referrer's commission
    commission_rate = Column(Float, nullable=False)  # Rate applied
    
    # Payout Status
    paid_out = Column(Boolean, default=False)
    paid_out_at = Column(DateTime)
    payout_method = Column(String(100))  # "agent_balance", "stripe_transfer", etc.
    payout_reference = Column(String(255))  # External payment ID
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "referral_id": str(self.referral_id),
            "referrer_agent_id": str(self.referrer_agent_id),
            "transaction_id": str(self.transaction_id),
            "transaction_amount_usd": self.transaction_amount_usd,
            "commission_amount_usd": self.commission_amount_usd,
            "commission_rate": self.commission_rate,
            "paid_out": self.paid_out,
            "paid_out_at": self.paid_out_at.isoformat() if self.paid_out_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


from typing import Dict
