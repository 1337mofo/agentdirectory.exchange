"""
AI Communication Monitor Endpoints
For Steve to monitor and participate in Nova/Boots conversations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from database.base import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])

class SendMessageRequest(BaseModel):
    from_user: str = "steve"
    to_agents: List[str]
    message: str

class MessageResponse(BaseModel):
    message_id: int
    from_agent_id: str
    from_agent_name: str
    to_agent_id: str
    message_text: str
    sent_at: datetime
    read_at: Optional[datetime]
    priority: str

class MonitorStatsResponse(BaseModel):
    total_messages: int
    nova_status: str
    boots_status: str

class MonitorDataResponse(BaseModel):
    messages: List[MessageResponse]
    stats: MonitorStatsResponse

@router.post("/send")
async def send_message(request: SendMessageRequest, db: Session = Depends(get_db)):
    """Send message from Steve to agents"""
    
    if not request.message:
        raise HTTPException(status_code=400, detail="Message required")
    
    # Register Steve if not exists
    db.execute(text("""
        INSERT INTO messaging_agents (agent_id, agent_name, instance_location, status)
        VALUES ('steve', 'Steve Eagle', 'Command Center', 'online')
        ON CONFLICT (agent_id) DO UPDATE SET 
            last_heartbeat = CURRENT_TIMESTAMP,
            status = 'online'
    """))
    
    # Send to each agent
    message_ids = []
    for to_agent in request.to_agents:
        result = db.execute(text("""
            INSERT INTO messaging_messages 
            (from_agent_id, to_agent_id, message_text, priority)
            VALUES ('steve', :to_agent, :message, 'high')
            RETURNING message_id
        """), {"to_agent": to_agent, "message": request.message})
        message_ids.append(result.fetchone()[0])
    
    db.commit()
    
    return {
        "status": "sent",
        "message_ids": message_ids
    }

@router.get("/messages")
async def get_monitor_data(db: Session = Depends(get_db)):
    """Get messages and stats for monitoring"""
    
    # Get messages (including Steve's messages)
    messages_result = db.execute(text("""
        SELECT 
            m.message_id,
            m.from_agent_id,
            fa.agent_name as from_agent_name,
            m.to_agent_id,
            m.message_text,
            m.sent_at,
            m.read_at,
            m.priority
        FROM messaging_messages m
        JOIN messaging_agents fa ON m.from_agent_id = fa.agent_id
        WHERE m.from_agent_id IN ('nova', 'boots', 'steve')
           OR m.to_agent_id IN ('nova', 'boots', 'steve')
        ORDER BY m.sent_at DESC
        LIMIT 100
    """))
    
    messages = []
    for row in messages_result:
        messages.append({
            "message_id": row.message_id,
            "from_agent_id": row.from_agent_id,
            "from_agent_name": row.from_agent_name,
            "to_agent_id": row.to_agent_id,
            "message_text": row.message_text,
            "sent_at": row.sent_at.isoformat(),
            "read_at": row.read_at.isoformat() if row.read_at else None,
            "priority": row.priority
        })
    
    # Get agent status
    agents_result = db.execute(text("""
        SELECT 
            agent_id,
            status,
            last_heartbeat,
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) as seconds_since
        FROM messaging_agents
        WHERE agent_id IN ('nova', 'boots')
    """))
    
    agents = {}
    for row in agents_result:
        agents[row.agent_id] = {
            "status": row.status,
            "seconds_since": row.seconds_since
        }
    
    # Determine status
    nova_status = "offline"
    boots_status = "offline"
    
    if "nova" in agents and agents["nova"]["seconds_since"] < 300:
        nova_status = "online"
    
    if "boots" in agents and agents["boots"]["seconds_since"] < 300:
        boots_status = "online"
    
    return {
        "messages": messages,
        "stats": {
            "total_messages": len(messages),
            "nova_status": nova_status,
            "boots_status": boots_status
        }
    }
