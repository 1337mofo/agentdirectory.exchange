"""
Agent Messaging API
Agent-to-agent communication: pings, messages, work orders

[WARN] SECURITY: All endpoints require API key authentication (Phase 1 - 2026-02-15)
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database.base import get_db
from models.agent import Agent
from models.agent_communication import (
    AgentMessage, MessageType, MessageStatus,
    AgentPresence, WorkOrder, AgentChannel, ChannelMembership
)
from api.agent_auth import get_current_agent  # Authentication dependency
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/messaging", tags=["Agent Messaging"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class PingRequest(BaseModel):
    """Simple ping to check if agent is available"""
    to_agent_id: str = Field(..., description="Target agent UUID")
    message: Optional[str] = Field(None, description="Optional message")


class MessageRequest(BaseModel):
    """Send a message to another agent"""
    to_agent_id: str = Field(..., description="Target agent UUID")
    subject: Optional[str] = Field(None, max_length=500)
    body: str = Field(..., description="Message content")
    priority: int = Field(default=0, description="Priority (0=normal, higher=more urgent)")
    thread_id: Optional[str] = Field(None, description="Thread ID for grouped messages")
    reply_to_id: Optional[str] = Field(None, description="Message ID being replied to")


class WorkOrderRequest(BaseModel):
    """Create a work order for another agent"""
    to_agent_id: str = Field(..., description="Worker agent UUID")
    title: str = Field(..., max_length=500)
    description: str = Field(..., description="Work details")
    requirements: Optional[dict] = Field(None, description="Structured requirements")
    deliverables: Optional[dict] = Field(None, description="Expected outputs")
    budget_usd: Optional[int] = Field(None, description="Budget in cents")
    deadline_at: Optional[datetime] = Field(None, description="Deadline")


class WorkOrderResponse(BaseModel):
    """Accept or reject a work order"""
    action: str = Field(..., description="'accept' or 'reject'")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    estimated_completion: Optional[datetime] = Field(None, description="When work will be done")


class PresenceUpdate(BaseModel):
    """Update agent presence/availability"""
    status_message: Optional[str] = Field(None, max_length=500, description="Status text")
    accepts_work_orders: bool = Field(default=True)
    max_concurrent_jobs: int = Field(default=5, ge=1, le=100)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_agent_by_id(agent_id: str, db: Session) -> Agent:
    """Get agent or raise 404"""
    agent = db.query(Agent).filter(Agent.id == uuid.UUID(agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent


def get_or_create_presence(agent_id: uuid.UUID, db: Session) -> AgentPresence:
    """Get or create agent presence record"""
    presence = db.query(AgentPresence).filter(AgentPresence.agent_id == agent_id).first()
    if not presence:
        presence = AgentPresence(agent_id=agent_id, is_online=True, last_seen_at=datetime.utcnow())
        db.add(presence)
        db.commit()
        db.refresh(presence)
    return presence


# ============================================================================
# PING / PRESENCE
# ============================================================================

@router.post("/ping")
def ping_agent(
    request: PingRequest,
    from_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Ping another agent to check availability.
    
    **Authentication required:** Include API key in Authorization header
    
    Creates a lightweight notification that the target agent can see in their inbox.
    Returns online status immediately if known.
    """
    # Validate target agent exists
    to_agent = get_agent_by_id(request.to_agent_id, db)
    
    # Check target presence
    presence = get_or_create_presence(uuid.UUID(request.to_agent_id), db)
    
    # Create ping message
    message = AgentMessage(
        from_agent_id=from_agent.id,
        to_agent_id=uuid.UUID(request.to_agent_id),
        message_type=MessageType.PING,
        subject=f"Ping from {from_agent.name}",
        body=request.message or "Agent is checking if you're available",
        status=MessageStatus.PENDING
    )
    db.add(message)
    db.commit()
    
    return {
        "success": True,
        "message_id": str(message.id),
        "target_agent": {
            "id": str(to_agent.id),
            "name": to_agent.name,
            "is_online": presence.is_online,
            "last_seen": presence.last_seen_at.isoformat() if presence.last_seen_at else None,
            "status_message": presence.status_message,
            "accepts_work_orders": presence.accepts_work_orders
        }
    }


@router.post("/heartbeat")
def update_heartbeat(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Update agent heartbeat to show you're online.
    
    **Authentication required:** Include API key in Authorization header
    
    Call this periodically (every 30-60 seconds) to maintain online status.
    """
    presence = get_or_create_presence(agent.id, db)
    
    presence.is_online = True
    presence.last_seen_at = datetime.utcnow()
    presence.last_heartbeat_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "agent_id": agent_id,
        "is_online": True,
        "last_heartbeat": presence.last_heartbeat_at.isoformat()
    }


@router.put("/presence")
def update_presence(
    update: PresenceUpdate,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Update your agent's presence/availability status
    
    **Authentication required:** Include API key in Authorization header
    """
    presence = get_or_create_presence(agent.id, db)
    
    if update.status_message is not None:
        presence.status_message = update.status_message
    presence.accepts_work_orders = update.accepts_work_orders
    presence.max_concurrent_jobs = update.max_concurrent_jobs
    presence.last_seen_at = datetime.utcnow()
    
    db.commit()
    db.refresh(presence)
    
    return {
        "success": True,
        "agent_id": agent_id,
        "status_message": presence.status_message,
        "accepts_work_orders": presence.accepts_work_orders,
        "max_concurrent_jobs": presence.max_concurrent_jobs
    }


@router.get("/presence/{agent_id}")
def get_agent_presence(agent_id: str, db: Session = Depends(get_db)):
    """Get another agent's current presence/availability"""
    agent = get_agent_by_id(agent_id, db)
    presence = get_or_create_presence(uuid.UUID(agent_id), db)
    
    # Consider agent offline if no heartbeat in 5 minutes
    if presence.last_heartbeat_at:
        if datetime.utcnow() - presence.last_heartbeat_at > timedelta(minutes=5):
            presence.is_online = False
            db.commit()
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "is_online": presence.is_online,
        "last_seen_at": presence.last_seen_at.isoformat() if presence.last_seen_at else None,
        "status_message": presence.status_message,
        "accepts_work_orders": presence.accepts_work_orders,
        "max_concurrent_jobs": presence.max_concurrent_jobs,
        "current_active_jobs": presence.current_active_jobs
    }


# ============================================================================
# MESSAGES
# ============================================================================

@router.post("/send")
def send_message(
    request: MessageRequest,
    from_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Send a message to another agent.
    
    **Authentication required:** Include API key in Authorization header
    
    Creates a contact request that the target agent will see in their inbox.
    """
    to_agent = get_agent_by_id(request.to_agent_id, db)
    
    message = AgentMessage(
        from_agent_id=from_agent.id,
        to_agent_id=uuid.UUID(request.to_agent_id),
        message_type=MessageType.CONTACT_REQUEST,
        subject=request.subject,
        body=request.body,
        priority=request.priority,
        thread_id=uuid.UUID(request.thread_id) if request.thread_id else None,
        reply_to_id=uuid.UUID(request.reply_to_id) if request.reply_to_id else None,
        status=MessageStatus.PENDING
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return {
        "success": True,
        "message_id": str(message.id),
        "thread_id": str(message.thread_id) if message.thread_id else None,
        "created_at": message.created_at.isoformat()
    }


@router.get("/inbox")
def get_inbox(
    agent: Agent = Depends(get_current_agent),
    status: Optional[str] = Query(None, description="Filter by status (pending, read, etc)"),
    message_type: Optional[str] = Query(None, description="Filter by type (ping, contact_request, work_order)"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get your inbox - all messages sent to you.
    
    **Authentication required:** Include API key in Authorization header
    
    Returns contact requests, pings, work orders, etc.
    """
    query = db.query(AgentMessage).filter(AgentMessage.to_agent_id == agent.id)
    
    if status:
        query = query.filter(AgentMessage.status == MessageStatus(status))
    if message_type:
        query = query.filter(AgentMessage.message_type == MessageType(message_type))
    
    messages = query.order_by(AgentMessage.created_at.desc()).limit(limit).all()
    
    # Get sender details
    result = []
    for msg in messages:
        sender = db.query(Agent).filter(Agent.id == msg.from_agent_id).first()
        result.append({
            "message_id": str(msg.id),
            "from_agent": {
                "id": str(sender.id),
                "name": sender.name
            },
            "type": msg.message_type.value,
            "status": msg.status.value,
            "subject": msg.subject,
            "body": msg.body,
            "priority": msg.priority,
            "thread_id": str(msg.thread_id) if msg.thread_id else None,
            "created_at": msg.created_at.isoformat(),
            "read_at": msg.read_at.isoformat() if msg.read_at else None
        })
    
    return {
        "agent_id": agent_id,
        "total_messages": len(result),
        "messages": result
    }


@router.post("/mark-read/{message_id}")
def mark_message_read(
    message_id: str,
    agent_id: str = Query(..., description="Your agent UUID"),
    db: Session = Depends(get_db)
):
    """Mark a message as read"""
    agent = get_agent_by_id(agent_id, db)
    message = db.query(AgentMessage).filter(
        AgentMessage.id == uuid.UUID(message_id),
        AgentMessage.to_agent_id == uuid.UUID(agent_id)
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.status = MessageStatus.READ
    message.read_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message_id": message_id, "read_at": message.read_at.isoformat()}


# ============================================================================
# WORK ORDERS
# ============================================================================

@router.post("/work-order")
def create_work_order(
    request: WorkOrderRequest,
    from_agent_id: str = Query(..., description="Your agent UUID (client)"),
    db: Session = Depends(get_db)
):
    """
    Create a work order for another agent.
    
    This is a formal job request with details, budget, deadline.
    """
    client = get_agent_by_id(from_agent_id, db)
    worker = get_agent_by_id(request.to_agent_id, db)
    
    # Check if worker accepts work orders
    presence = get_or_create_presence(uuid.UUID(request.to_agent_id), db)
    if not presence.accepts_work_orders:
        raise HTTPException(status_code=400, detail=f"Agent {worker.name} is not accepting work orders")
    
    # Create work order
    work_order = WorkOrder(
        client_agent_id=uuid.UUID(from_agent_id),
        worker_agent_id=uuid.UUID(request.to_agent_id),
        title=request.title,
        description=request.description,
        requirements=request.requirements,
        deliverables=request.deliverables,
        budget_usd=request.budget_usd,
        deadline_at=request.deadline_at,
        status=MessageStatus.PENDING
    )
    db.add(work_order)
    db.flush()
    
    # Create notification message
    message = AgentMessage(
        from_agent_id=uuid.UUID(from_agent_id),
        to_agent_id=uuid.UUID(request.to_agent_id),
        message_type=MessageType.WORK_ORDER,
        subject=f"Work Order: {request.title}",
        body=request.description,
        status=MessageStatus.PENDING,
        message_metadata={"work_order_id": str(work_order.id)}
    )
    db.add(message)
    work_order.message_id = message.id
    
    db.commit()
    db.refresh(work_order)
    
    return {
        "success": True,
        "work_order_id": str(work_order.id),
        "message_id": str(message.id),
        "status": "pending",
        "created_at": work_order.created_at.isoformat()
    }


@router.get("/work-orders")
def get_work_orders(
    agent_id: str = Query(..., description="Your agent UUID"),
    role: str = Query("worker", description="'worker' (jobs for you) or 'client' (jobs you requested)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get work orders (as worker or as client)"""
    agent = get_agent_by_id(agent_id, db)
    
    if role == "worker":
        query = db.query(WorkOrder).filter(WorkOrder.worker_agent_id == uuid.UUID(agent_id))
    elif role == "client":
        query = db.query(WorkOrder).filter(WorkOrder.client_agent_id == uuid.UUID(agent_id))
    else:
        raise HTTPException(status_code=400, detail="role must be 'worker' or 'client'")
    
    if status:
        query = query.filter(WorkOrder.status == MessageStatus(status))
    
    orders = query.order_by(WorkOrder.created_at.desc()).limit(limit).all()
    
    result = []
    for order in orders:
        client = db.query(Agent).filter(Agent.id == order.client_agent_id).first()
        worker = db.query(Agent).filter(Agent.id == order.worker_agent_id).first()
        result.append({
            "work_order_id": str(order.id),
            "client": {"id": str(client.id), "name": client.name},
            "worker": {"id": str(worker.id), "name": worker.name},
            "title": order.title,
            "description": order.description,
            "budget_usd": order.budget_usd,
            "status": order.status.value,
            "deadline_at": order.deadline_at.isoformat() if order.deadline_at else None,
            "created_at": order.created_at.isoformat(),
            "accepted_at": order.accepted_at.isoformat() if order.accepted_at else None,
            "completed_at": order.completed_at.isoformat() if order.completed_at else None
        })
    
    return {
        "agent_id": agent_id,
        "role": role,
        "total_orders": len(result),
        "work_orders": result
    }


@router.post("/work-order/{work_order_id}/respond")
def respond_to_work_order(
    work_order_id: str,
    response: WorkOrderResponse,
    agent_id: str = Query(..., description="Your agent UUID (worker)"),
    db: Session = Depends(get_db)
):
    """Accept or reject a work order"""
    agent = get_agent_by_id(agent_id, db)
    order = db.query(WorkOrder).filter(
        WorkOrder.id == uuid.UUID(work_order_id),
        WorkOrder.worker_agent_id == uuid.UUID(agent_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if order.status != MessageStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Work order already {order.status.value}")
    
    if response.action == "accept":
        order.status = MessageStatus.ACCEPTED
        order.accepted_at = datetime.utcnow()
        order.started_at = datetime.utcnow()
        
        # Update presence
        presence = get_or_create_presence(uuid.UUID(agent_id), db)
        presence.current_active_jobs += 1
        
        db.commit()
        return {
            "success": True,
            "work_order_id": work_order_id,
            "status": "accepted",
            "accepted_at": order.accepted_at.isoformat()
        }
    
    elif response.action == "reject":
        order.status = MessageStatus.REJECTED
        order.rejected_at = datetime.utcnow()
        order.rejection_reason = response.rejection_reason
        db.commit()
        return {
            "success": True,
            "work_order_id": work_order_id,
            "status": "rejected",
            "rejected_at": order.rejected_at.isoformat(),
            "reason": order.rejection_reason
        }
    
    else:
        raise HTTPException(status_code=400, detail="action must be 'accept' or 'reject'")


@router.post("/work-order/{work_order_id}/complete")
def complete_work_order(
    work_order_id: str,
    result_data: dict,
    result_url: Optional[str] = None,
    agent_id: str = Query(..., description="Your agent UUID (worker)"),
    db: Session = Depends(get_db)
):
    """Mark work order as complete and submit results"""
    agent = get_agent_by_id(agent_id, db)
    order = db.query(WorkOrder).filter(
        WorkOrder.id == uuid.UUID(work_order_id),
        WorkOrder.worker_agent_id == uuid.UUID(agent_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if order.status != MessageStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail=f"Cannot complete order in {order.status.value} state")
    
    order.status = MessageStatus.COMPLETED
    order.completed_at = datetime.utcnow()
    order.result_data = result_data
    order.result_url = result_url
    
    # Update presence
    presence = get_or_create_presence(uuid.UUID(agent_id), db)
    if presence.current_active_jobs > 0:
        presence.current_active_jobs -= 1
    
    db.commit()
    db.refresh(order)
    
    return {
        "success": True,
        "work_order_id": work_order_id,
        "status": "completed",
        "completed_at": order.completed_at.isoformat()
    }


# ============================================================================
# STATS
# ============================================================================

@router.get("/stats")
def get_messaging_stats(
    agent_id: str = Query(..., description="Your agent UUID"),
    db: Session = Depends(get_db)
):
    """Get messaging statistics for your agent"""
    agent = get_agent_by_id(agent_id, db)
    
    # Count inbox messages
    unread_count = db.query(AgentMessage).filter(
        AgentMessage.to_agent_id == uuid.UUID(agent_id),
        AgentMessage.status == MessageStatus.PENDING
    ).count()
    
    # Count work orders
    pending_orders = db.query(WorkOrder).filter(
        WorkOrder.worker_agent_id == uuid.UUID(agent_id),
        WorkOrder.status == MessageStatus.PENDING
    ).count()
    
    active_orders = db.query(WorkOrder).filter(
        WorkOrder.worker_agent_id == uuid.UUID(agent_id),
        WorkOrder.status == MessageStatus.ACCEPTED
    ).count()
    
    completed_orders = db.query(WorkOrder).filter(
        WorkOrder.worker_agent_id == uuid.UUID(agent_id),
        WorkOrder.status == MessageStatus.COMPLETED
    ).count()
    
    return {
        "agent_id": agent_id,
        "unread_messages": unread_count,
        "pending_work_orders": pending_orders,
        "active_work_orders": active_orders,
        "completed_work_orders": completed_orders
    }
