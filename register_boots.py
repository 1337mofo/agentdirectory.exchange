"""
Register Boots Eagle as an agent on agentdirectory.exchange
"""
import sys
sys.path.append('C:\\Users\\ADMIN\\.openclaw\\workspace\\agentdirectory.exchange\\backend')

from database.base import get_session_local
from models.agent import Agent, AgentType, VerificationStatus
from models.agent_communication import AgentPresence
from datetime import datetime
import uuid

def register_boots():
    """Register Boots Eagle as an agent"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    # Check if Boots already exists
    existing = db.query(Agent).filter(Agent.name == "Boots Eagle").first()
    if existing:
        print(f"✅ Boots already registered: {existing.id}")
        print(f"   Name: {existing.name}")
        print(f"   Type: {existing.agent_type}")
        print(f"   Status: {existing.verification_status}")
        return existing
    
    # Create Boots agent
    boots = Agent(
        name="Boots Eagle",
        description="Tactical AI for Eagle Family Office - Mobile operations, Surface Pro 6 deployment, field execution",
        agent_type=AgentType.HYBRID,
        owner_email="steve@theaerie.ai",
        capabilities=[
            "tactical_execution",
            "mobile_support", 
            "surface_operations",
            "field_deployment",
            "rapid_response"
        ],
        pricing_model={
            "internal": True,
            "eagle_family": True
        },
        verification_status=VerificationStatus.EAGLE_OFFICIAL,
        verified=True,
        badges=["eagle_family", "tactical", "mobile"],
        is_active=True
    )
    
    db.add(boots)
    db.commit()
    db.refresh(boots)
    
    # Create presence record
    presence = AgentPresence(
        agent_id=boots.id,
        is_online=False,  # Currently offline
        status_message="Awaiting startup - needs Anthropic API key",
        accepts_work_orders=True,
        max_concurrent_jobs=3,
        last_seen_at=datetime.utcnow()
    )
    
    db.add(presence)
    db.commit()
    
    print(f"✅ Boots Eagle registered successfully!")
    print(f"   Agent ID: {boots.id}")
    print(f"   Name: {boots.name}")
    print(f"   Type: {boots.agent_type}")
    print(f"   Status: {boots.verification_status}")
    print(f"   Presence: Offline (awaiting startup)")
    
    return boots

if __name__ == "__main__":
    register_boots()
