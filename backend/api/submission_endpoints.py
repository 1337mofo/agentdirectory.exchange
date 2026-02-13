"""
Agent Submission Endpoints - Public submission with manual review
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import uuid
from datetime import datetime

from database.base import get_db
from models.agent import Agent

router = APIRouter(prefix="/api/v1/submissions", tags=["submissions"])


class PricingModel(BaseModel):
    """Pricing information"""
    model: str = Field(..., description="per_request, per_token, subscription, etc.")
    price_usd: float = Field(..., ge=0, description="Price in USD")


class AgentSubmission(BaseModel):
    """Public agent submission schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    website: str = Field(..., min_length=1, max_length=500, description="GitHub, HuggingFace, or website URL")
    email: EmailStr = Field(..., description="Contact email")
    api_endpoint: Optional[str] = Field(None, max_length=500)
    capabilities: list = Field(..., min_items=1, description="List of agent capabilities")
    pricing: PricingModel
    
    @validator('website', 'api_endpoint')
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class AgentSubmissionResponse(BaseModel):
    """Response after submission"""
    success: bool
    message: str
    submission_id: Optional[str] = None


@router.post("/submit", response_model=AgentSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_agent_for_review(
    submission: AgentSubmission,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for agent submission
    
    Flow:
    1. Accept submission from web form
    2. Store in database with pending_review status
    3. Send notification to admin (Steve)
    4. Return submission confirmation
    
    Admin reviews and approves via dashboard or API
    """
    try:
        # Create agent record with pending status
        agent_id = str(uuid.uuid4())
        
        # Convert agent_type from pricing model if needed
        from models.agent import AgentType
        agent_type_enum = AgentType.API  # Default for submitted agents
        
        # Create pricing JSON
        pricing_data = {
            "model": submission.pricing.model,
            "price_usd": submission.pricing.price_usd
        }
        
        # Create agent in database (inactive, pending review)
        new_agent = Agent(
            id=agent_id,
            name=submission.name,
            description=submission.description,
            source_url=submission.website,
            owner_email=submission.email,
            api_endpoint=submission.api_endpoint,
            capabilities=submission.capabilities,
            pricing_model=pricing_data,
            # Status fields
            is_active=False,  # Not active until approved
            verified=False,
            pending_review=True,
            submission_source="web_form",
            # Metadata
            agent_type=agent_type_enum,
            categories=None,  # Will be assigned during review
            auto_discovered=False,
            quality_score=70,  # Default quality score for manual submissions
            created_at=datetime.utcnow()
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        # TODO: Send notification to Steve via Telegram
        # await notify_admin_of_submission(submission, agent_id)
        
        return AgentSubmissionResponse(
            success=True,
            message="Agent submitted successfully! We'll review it within 24-48 hours and contact you at the email provided.",
            submission_id=agent_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing submission: {str(e)}"
        )


@router.get("/submissions/pending")
async def list_pending_submissions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all pending agent submissions (admin only - TODO: add auth)
    """
    try:
        query = db.query(Agent).filter(
            Agent.pending_review == True,
            Agent.is_active == False
        ).order_by(Agent.created_at.desc())
        
        total = query.count()
        submissions = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "submissions": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "source_url": agent.source_url,
                    "owner_email": agent.owner_email,
                    "agent_type": agent.agent_type,
                    "categories": agent.categories,
                    "submitted_at": agent.created_at.isoformat() if agent.created_at else None
                }
                for agent in submissions
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching submissions: {str(e)}"
        )


@router.post("/submissions/{submission_id}/approve")
async def approve_submission(
    submission_id: str,
    db: Session = Depends(get_db)
):
    """
    Approve a pending agent submission (admin only - TODO: add auth)
    
    Makes the agent active and visible in directory
    """
    try:
        agent = db.query(Agent).filter(Agent.id == submission_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        if not agent.pending_review:
            raise HTTPException(status_code=400, detail="Agent is not pending review")
        
        # Approve the agent
        agent.pending_review = False
        agent.is_active = True
        agent.verified = True
        agent.approved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(agent)
        
        # TODO: Send notification to submitter
        # await notify_submitter_of_approval(agent.owner_email, agent.name)
        
        return {
            "success": True,
            "message": f"Agent '{agent.name}' approved and activated",
            "agent_id": agent.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving submission: {str(e)}"
        )


@router.post("/submissions/{submission_id}/reject")
async def reject_submission(
    submission_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Reject a pending agent submission (admin only - TODO: add auth)
    
    Keeps record but marks as rejected
    """
    try:
        agent = db.query(Agent).filter(Agent.id == submission_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        if not agent.pending_review:
            raise HTTPException(status_code=400, detail="Agent is not pending review")
        
        # Reject the agent
        agent.pending_review = False
        agent.is_active = False
        agent.verified = False
        agent.rejection_reason = reason
        agent.rejected_at = datetime.utcnow()
        
        db.commit()
        
        # TODO: Send notification to submitter with reason
        # await notify_submitter_of_rejection(agent.owner_email, agent.name, reason)
        
        return {
            "success": True,
            "message": f"Agent '{agent.name}' rejected",
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting submission: {str(e)}"
        )


async def notify_admin_of_submission(submission: AgentSubmission, agent_id: str):
    """
    Send Telegram notification to Steve about new submission
    TODO: Integrate with Telegram bot
    """
    message = f"""
🆕 New Agent Submission

Name: {submission.name}
Type: {submission.agent_type}
Owner: {submission.owner_email}

Description: {submission.description[:200]}...

Source: {submission.source_url}

Review at: /api/v1/agents/submissions/{agent_id}
Approve: /api/v1/agents/submissions/{agent_id}/approve
Reject: /api/v1/agents/submissions/{agent_id}/reject
"""
    # TODO: Send via Telegram
    pass


async def notify_submitter_of_approval(email: str, agent_name: str):
    """
    Email submitter that their agent was approved
    TODO: Integrate with email service
    """
    pass


async def notify_submitter_of_rejection(email: str, agent_name: str, reason: str):
    """
    Email submitter that their agent was rejected with reason
    TODO: Integrate with email service
    """
    pass
