"""
MCP Tool Listing Model
"""
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from database.base import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    author_agent_id = Column(String(36), nullable=False, index=True)
    package_name = Column(String(255), unique=True, nullable=False)
    install_command = Column(String(500), nullable=True)
    modules = Column(JSON, nullable=True)
    pricing_model = Column(String(50), nullable=False, default="free")  # free/subscription/per_call/one_time
    price_usd = Column(Float, nullable=True, default=0.0)
    monthly_price_usd = Column(Float, nullable=True, default=0.0)
    per_call_price_usd = Column(Float, nullable=True, default=0.0)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)
    protocol = Column(String(50), nullable=False, default="mcp")  # mcp/a2a/openai/langchain
    version = Column(String(50), nullable=True)
    repository_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    total_installs = Column(Integer, nullable=False, default=0)
    total_calls = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GroupBuyingPool(Base):
    __tablename__ = "group_buying_pools"

    id = Column(String(36), primary_key=True)
    service_id = Column(String(36), nullable=False, index=True)
    creator_agent_id = Column(String(36), nullable=False)
    target_quantity = Column(Integer, nullable=False)
    current_quantity = Column(Integer, nullable=False, default=0)
    discount_tier = Column(String(50), nullable=False)  # e.g. "10%", "20%", "30%"
    participants = Column(JSON, nullable=True, default=[])
    status = Column(String(50), nullable=False, default="active")  # active/triggered/expired/cancelled
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
