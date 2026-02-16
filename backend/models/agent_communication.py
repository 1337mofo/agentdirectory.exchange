"""
Agent Communication Models
Agent-to-agent messaging, pings, contact requests, and work orders
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from database.base import Base


class MessageType(str, enum.Enum):
    """Type of message between agents"""
    PING = "ping"  # Simple "are you there" check
    CONTACT_REQUEST = "contact_request"  # "I want to talk to you"
    WORK_ORDER = "work_order"  # "I have a job for you"
    CHAT_MESSAGE = "chat_message"  # Direct message
    NOTIFICATION = "notification"  # System notification


class MessageStatus(str, enum.Enum):
    """Status of message"""
    PENDING = "pending"  # Not yet seen
    DELIVERED = "delivered"  # Agent received notification
    READ = "read"  # Agent opened/read message
    ACCEPTED = "accepted"  # Agent accepted work order
    REJECTED = "rejected"  # Agent rejected work order
    COMPLETED = "completed"  # Work order completed


class AgentMessage(Base):
    """Agent-to-agent messages"""
    __tablename__ = "agent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Sender and receiver
    from_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    to_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    
    # Message details
    message_type = Column(SQLEnum(MessageType), nullable=False)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    subject = Column(String(500))  # Optional subject line
    body = Column(Text)  # Message content
    
    # Metadata
    message_metadata = Column(JSON)  # Additional data (work order details, attachments, etc.)
    priority = Column(Integer, default=0)  # Higher = more important
    expires_at = Column(DateTime)  # Optional expiration
    
    # Threading
    thread_id = Column(UUID(as_uuid=True))  # Group related messages
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("agent_messages.id"))  # Reply threading
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    responded_at = Column(DateTime)
    
    # Indexes for fast queries
    def __repr__(self):
        return f"<AgentMessage {self.id} from={self.from_agent_id} to={self.to_agent_id} type={self.message_type}>"


class AgentPresence(Base):
    """Track agent online/offline status"""
    __tablename__ = "agent_presence"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), primary_key=True)
    
    # Status
    is_online = Column(Boolean, default=False, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_message = Column(String(500))  # "Available", "Busy", "Away", custom message
    
    # Connection info
    websocket_connected = Column(Boolean, default=False)
    last_heartbeat_at = Column(DateTime)
    
    # Availability
    accepts_work_orders = Column(Boolean, default=True)
    max_concurrent_jobs = Column(Integer, default=5)
    current_active_jobs = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AgentPresence {self.agent_id} online={self.is_online}>"


class WorkOrder(Base):
    """Formal work request from one agent to another"""
    __tablename__ = "work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Parties
    client_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    worker_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    
    # Work details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSON)  # Structured requirements
    deliverables = Column(JSON)  # Expected outputs
    
    # Pricing
    budget_usd = Column(Integer)  # Budget in cents
    actual_cost_usd = Column(Integer)  # Final cost in cents
    
    # Status tracking
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    
    # Timing
    deadline_at = Column(DateTime)
    accepted_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Results
    result_data = Column(JSON)  # Output data
    result_url = Column(String(1000))  # Download link if large
    
    # Related message
    message_id = Column(UUID(as_uuid=True), ForeignKey("agent_messages.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<WorkOrder {self.id} client={self.client_agent_id} worker={self.worker_agent_id} status={self.status}>"


class AgentChannel(Base):
    """Chat channels for agent groups/teams"""
    __tablename__ = "agent_channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Channel details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    channel_type = Column(String(50), default="group")  # "group", "direct", "team"
    
    # Settings
    is_private = Column(Boolean, default=False)
    max_members = Column(Integer)
    
    # Metadata
    channel_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AgentChannel {self.id} name={self.name}>"


class ChannelMembership(Base):
    """Agent membership in channels"""
    __tablename__ = "channel_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    channel_id = Column(UUID(as_uuid=True), ForeignKey("agent_channels.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    
    # Role
    role = Column(String(50), default="member")  # "owner", "admin", "member"
    
    # Notifications
    notifications_enabled = Column(Boolean, default=True)
    last_read_at = Column(DateTime)
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ChannelMembership channel={self.channel_id} agent={self.agent_id}>"
