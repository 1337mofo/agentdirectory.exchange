"""
Transaction Model - Payment history between agents
"""
from sqlalchemy import Column, String, Float, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum

from database.base import Base


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    CAPABILITY_PURCHASE = "capability_purchase"
    SERVICE_REQUEST = "service_request"
    SUBSCRIPTION = "subscription"


class TransactionStatus(str, Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction(Base):
    """
    USDC payment transaction between agents
    """
    __tablename__ = "transactions"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transaction parties
    sender_agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False, index=True)
    recipient_agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False, index=True)
    
    # Solana blockchain data
    signature = Column(String(88), nullable=False, unique=True, index=True)
    block_time = Column(DateTime)
    slot = Column(BigInteger)
    
    # Amounts
    amount_usdc = Column(Float, nullable=False)
    commission_usdc = Column(Float, nullable=False)
    recipient_received_usdc = Column(Float, nullable=False)
    
    # Transaction details
    service_description = Column(Text)
    status = Column(String(20), nullable=False, default='pending', index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime)
    failed_reason = Column(Text)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "sender_agent_id": str(self.sender_agent_id),
            "recipient_agent_id": str(self.recipient_agent_id),
            "signature": self.signature,
            "amount_usdc": self.amount_usdc,
            "commission_usdc": self.commission_usdc,
            "recipient_received_usdc": self.recipient_received_usdc,
            "service_description": self.service_description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "explorer_url": f"https://solscan.io/tx/{self.signature}",
            "failed_reason": self.failed_reason
        }
