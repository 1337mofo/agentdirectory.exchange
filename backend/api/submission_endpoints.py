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
    Public endpoint for agent submission with 100% agentic review
    
    Flow:
    1. Accept submission from web form
    2. Run agentic review (anti-spam, quality check, validation)
    3. Auto-approve or auto-reject
    4. Notify submitter of decision
    5. Log to Steve via Telegram (summary only)
    """
    try:
        # Import agentic reviewer
        from services.agentic_reviewer import AgenticReviewer
        
        # Run autonomous review
        reviewer = AgenticReviewer(db)
        submission_dict = {
            'name': submission.name,
            'description': submission.description,
            'website': submission.website,
            'email': submission.email,
            'api_endpoint': submission.api_endpoint,
            'capabilities': submission.capabilities
        }
        
        should_approve, review_reason, quality_score = reviewer.review_submission(submission_dict)
        
        # Create agent record
        agent_id = str(uuid.uuid4())
        
        from models.agent import AgentType
        agent_type_enum = AgentType.API
        
        pricing_data = {
            "model": submission.pricing.model,
            "price_usd": submission.pricing.price_usd
        }
        
        # Create agent with review decision
        new_agent = Agent(
            id=agent_id,
            name=submission.name,
            description=submission.description,
            source_url=submission.website,
            owner_email=submission.email,
            api_endpoint=submission.api_endpoint,
            capabilities=submission.capabilities,
            pricing_model=pricing_data,
            # Status based on agentic review
            is_active=should_approve,  # Auto-activate if approved
            verified=should_approve,
            pending_review=False,  # No manual review needed
            submission_source="web_form",
            # Metadata
            agent_type=agent_type_enum,
            categories=None,  # Auto-assign from capabilities later
            auto_discovered=False,
            quality_score=quality_score,
            review_reason=review_reason,
            reviewed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        # Send notification to submitter
        await notify_submitter_of_decision(
            email=submission.email,
            agent_name=submission.name,
            approved=should_approve,
            reason=review_reason,
            quality_score=quality_score
        )
        
        # Log to Steve (summary only, not every submission)
        if not should_approve or quality_score >= 90:
            # Only notify Steve of rejections or exceptional approvals
            await notify_admin_of_review(
                submission=submission,
                agent_id=agent_id,
                approved=should_approve,
                reason=review_reason,
                quality_score=quality_score
            )
        
        # Response to submitter
        if should_approve:
            message = f"🎉 Your agent '{submission.name}' has been approved and is now live on Agent Directory Exchange! Quality score: {quality_score}/100. Check it out at https://agentdirectory.exchange/"
        else:
            message = f"Thank you for your submission. Unfortunately, '{submission.name}' did not meet our quality standards. Reason: {review_reason}. You can resubmit after addressing these issues."
        
        return AgentSubmissionResponse(
            success=should_approve,
            message=message,
            submission_id=agent_id if should_approve else None
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


async def notify_admin_of_review(
    submission: AgentSubmission,
    agent_id: str,
    approved: bool,
    reason: str,
    quality_score: int
):
    """
    Send Telegram notification to Steve about agentic review
    Only for rejections or exceptional approvals (90+ score)
    """
    import os
    
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = "1921452767"  # Steve Eagle
    
    if not TELEGRAM_BOT_TOKEN:
        return  # Silently skip if not configured
    
    status_emoji = "✅" if approved else "❌"
    status_text = "AUTO-APPROVED" if approved else "AUTO-REJECTED"
    
    message = f"""{status_emoji} **Agent Submission {status_text}**

**{submission.name}**
Quality Score: {quality_score}/100

Owner: {submission.email}
Website: {submission.website}

Decision: {reason}

Capabilities: {', '.join(submission.capabilities[:5])}

{"✨ Now live on directory" if approved else "🚫 Not listed"}
"""
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=5)
    except Exception as e:
        print(f"Telegram notification failed: {e}")


async def notify_submitter_of_decision(
    email: str,
    agent_name: str,
    approved: bool,
    reason: str,
    quality_score: int
):
    """
    Email submitter with agentic review decision
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    
    # Email configuration (GoDaddy SMTP)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtpout.secureserver.net")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "nova@agentdirectory.exchange")
    FROM_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    if not FROM_PASSWORD:
        print(f"WARNING: SMTP_PASSWORD not configured, email notification skipped for {email}")
        return
    
    try:
        if approved:
            subject = f"✅ Your agent '{agent_name}' is now live!"
            body = f"""
Hi there,

Great news! Your agent "{agent_name}" has been approved and is now live on Agent Directory Exchange.

Quality Score: {quality_score}/100
Review: {reason}

Your agent is now discoverable at:
https://agentdirectory.exchange/

Next steps:
• Share your agent listing with your network
• Monitor performance via our analytics
• Update your agent details anytime

Questions? Just reply to this email.

Best regards,
Nova
Agent Directory Exchange Team

---
This is an automated message from our agentic review system.
"""
        else:
            subject = f"Submission Update: {agent_name}"
            body = f"""
Hi there,

Thank you for submitting "{agent_name}" to Agent Directory Exchange.

Our automated review system has flagged some issues that need attention:

Quality Score: {quality_score}/100
Review Feedback: {reason}

What you can do:
• Address the feedback above
• Improve your agent's description and documentation
• Resubmit when ready (we welcome resubmissions!)

Need help? Reply to this email and we'll assist you.

Best regards,
Nova
Agent Directory Exchange Team

---
This is an automated message from our agentic review system.
"""
        
        msg = MIMEMultipart()
        msg['From'] = f"Nova @ Agent Directory <{FROM_EMAIL}>"
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent to {email}: {subject}")
        
    except Exception as e:
        print(f"Email notification failed for {email}: {e}")
        # Don't fail the submission if email fails
