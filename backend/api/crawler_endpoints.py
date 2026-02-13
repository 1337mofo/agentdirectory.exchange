"""
Crawler Automation Endpoints - Admin API for automated agent discovery uploads
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uuid
from datetime import datetime

from database.base import get_db
from models.agent import Agent
from api.auth import verify_admin_api_key

router = APIRouter(prefix="/api/v1/crawler", tags=["crawler"])


class CrawlerAgentSubmit(BaseModel):
    """Schema for crawler-discovered agent submission"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    source_url: str = Field(..., min_length=1, max_length=500)
    discovery_source: str = Field(..., min_length=1, max_length=100)  # "huggingface", "github", etc.
    quality_score: int = Field(default=50, ge=0, le=100)
    agent_type: Optional[str] = None
    categories: Optional[List[str]] = None
    
    @validator('source_url')
    def validate_url(cls, v):
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class CrawlerBatchSubmit(BaseModel):
    """Schema for batch agent submission from crawler"""
    agents: List[CrawlerAgentSubmit]
    crawler_run_id: Optional[str] = None
    dry_run: bool = False


class CrawlerSubmitResponse(BaseModel):
    """Response after crawler submission"""
    success: bool
    message: str
    agents_submitted: int
    agents_created: int
    agents_skipped: int
    skipped_reasons: Optional[dict] = None
    created_ids: Optional[List[str]] = None


@router.post("/submit", response_model=CrawlerSubmitResponse, status_code=status.HTTP_201_CREATED)
async def crawler_submit_agents(
    submission: CrawlerBatchSubmit,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_api_key)
):
    """
    Admin-only endpoint for automated crawler to submit discovered agents
    
    Requires: Authorization: Bearer <ADMIN_API_KEY>
    
    Flow:
    1. Authenticate admin API key
    2. Validate agent data
    3. Check for duplicates (by source_url)
    4. Create agents with auto_discovered=TRUE
    5. Set quality threshold (quality_score >= 50 auto-approved)
    6. Return summary of created/skipped agents
    """
    created_ids = []
    skipped = 0
    skipped_reasons = {}
    
    try:
        for agent_data in submission.agents:
            # Check for duplicate by source_url
            existing = db.query(Agent).filter(Agent.source_url == agent_data.source_url).first()
            
            if existing:
                skipped += 1
                reason = f"Duplicate source_url: {agent_data.source_url}"
                skipped_reasons[agent_data.name] = reason
                continue
            
            # Quality filter - skip low quality agents
            if agent_data.quality_score < 50:
                skipped += 1
                reason = f"Quality score too low: {agent_data.quality_score}"
                skipped_reasons[agent_data.name] = reason
                continue
            
            # Dry run mode - don't actually create
            if submission.dry_run:
                continue
            
            # Create agent
            agent_id = str(uuid.uuid4())
            
            # Auto-approve high quality agents (score >= 70)
            auto_approve = agent_data.quality_score >= 70
            
            new_agent = Agent(
                id=agent_id,
                name=agent_data.name,
                description=agent_data.description,
                source_url=agent_data.source_url,
                # Auto-discovery flags
                auto_discovered=True,
                submission_source=agent_data.discovery_source,
                # Quality scoring
                quality_score=agent_data.quality_score,
                # Approval status
                is_active=auto_approve,
                verified=auto_approve,
                pending_review=not auto_approve,
                approved_at=datetime.utcnow() if auto_approve else None,
                # Metadata
                agent_type=agent_data.agent_type,
                categories=agent_data.categories,
                created_at=datetime.utcnow()
            )
            
            db.add(new_agent)
            created_ids.append(agent_id)
        
        # Commit all at once
        if not submission.dry_run:
            db.commit()
        
        agents_created = len(created_ids)
        agents_submitted = len(submission.agents)
        
        message = f"Processed {agents_submitted} agents: {agents_created} created, {skipped} skipped"
        if submission.dry_run:
            message = f"DRY RUN: Would create {agents_created} agents, skip {skipped}"
        
        return CrawlerSubmitResponse(
            success=True,
            message=message,
            agents_submitted=agents_submitted,
            agents_created=agents_created,
            agents_skipped=skipped,
            skipped_reasons=skipped_reasons if skipped > 0 else None,
            created_ids=created_ids if not submission.dry_run else None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing crawler submission: {str(e)}"
        )


@router.get("/stats")
async def get_crawler_stats(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_api_key)
):
    """
    Get statistics about auto-discovered agents
    Admin-only endpoint
    """
    try:
        # Count auto-discovered agents
        total_discovered = db.query(Agent).filter(Agent.auto_discovered == True).count()
        
        # Count by source
        from sqlalchemy import func
        by_source = db.query(
            Agent.submission_source,
            func.count(Agent.id).label('count')
        ).filter(
            Agent.auto_discovered == True
        ).group_by(
            Agent.submission_source
        ).all()
        
        # Count pending review
        pending_review = db.query(Agent).filter(
            Agent.auto_discovered == True,
            Agent.pending_review == True
        ).count()
        
        # Count auto-approved
        auto_approved = db.query(Agent).filter(
            Agent.auto_discovered == True,
            Agent.is_active == True,
            Agent.verified == True
        ).count()
        
        # Average quality score
        avg_quality = db.query(func.avg(Agent.quality_score)).filter(
            Agent.auto_discovered == True
        ).scalar()
        
        return {
            "success": True,
            "total_discovered": total_discovered,
            "by_source": {source: count for source, count in by_source},
            "pending_review": pending_review,
            "auto_approved": auto_approved,
            "average_quality_score": round(float(avg_quality), 2) if avg_quality else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching crawler stats: {str(e)}"
        )


@router.post("/approve-pending")
async def approve_pending_discovered(
    min_quality_score: int = 60,
    limit: int = 100,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_api_key)
):
    """
    Bulk approve pending auto-discovered agents above quality threshold
    Admin-only endpoint
    """
    try:
        # Find pending agents above quality threshold
        pending_agents = db.query(Agent).filter(
            Agent.auto_discovered == True,
            Agent.pending_review == True,
            Agent.quality_score >= min_quality_score
        ).limit(limit).all()
        
        approved_count = 0
        approved_ids = []
        
        for agent in pending_agents:
            agent.pending_review = False
            agent.is_active = True
            agent.verified = True
            agent.approved_at = datetime.utcnow()
            approved_count += 1
            approved_ids.append(str(agent.id))
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Approved {approved_count} agents",
            "approved_count": approved_count,
            "approved_ids": approved_ids
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving pending agents: {str(e)}"
        )
