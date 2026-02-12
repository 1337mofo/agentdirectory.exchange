"""
Request & Bid API Endpoints - Reverse Marketplace
Agents post needs, others bid to fulfill
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from database.base import get_db
from models.agent import Agent
from models.request import Request, RequestStatus, RequestUrgency
from models.bid import Bid, BidStatus
from models.transaction import Transaction, TransactionType, TransactionStatus

router = APIRouter(prefix="/api/v1", tags=["Requests & Bids"])


# ==========================================
# Request Schemas
# ==========================================

class RequestCreate(BaseModel):
    title: str = Field(..., min_length=10, max_length=500)
    description: str = Field(..., min_length=50)
    category: Optional[str] = None
    required_capabilities: Optional[list] = None
    tags: Optional[list] = None
    budget_min_usd: float = Field(..., gt=0)
    budget_max_usd: float = Field(..., gt=0)
    urgency: RequestUrgency = RequestUrgency.MEDIUM
    deadline_hours: int = Field(24, gt=0)  # Hours from now
    expected_output: str
    input_data: Optional[dict] = None
    is_public: bool = True


class BidCreate(BaseModel):
    request_id: str
    price_usd: float = Field(..., gt=0)
    estimated_delivery_hours: float = Field(..., gt=0)
    proposal: str = Field(..., min_length=100)
    approach: Optional[str] = None
    sample_work_url: Optional[str] = None
    includes: Optional[list] = None
    revisions_included: int = 1
    guarantee: Optional[str] = None


class BidAccept(BaseModel):
    bid_id: str
    message: Optional[str] = None


# ==========================================
# Request Endpoints
# ==========================================

@router.post("/requests", status_code=status.HTTP_201_CREATED)
def create_request(request_data: RequestCreate, db: Session = Depends(get_db)):
    """
    Post a need - other agents will bid to fulfill it
    
    Reverse marketplace: "I need X done, who can do it?"
    """
    # Calculate deadline and expiration
    deadline = datetime.utcnow() + timedelta(hours=request_data.deadline_hours)
    expires_at = deadline + timedelta(hours=24)  # Give extra time for selection
    
    # Create request
    request = Request(
        title=request_data.title,
        description=request_data.description,
        category=request_data.category,
        required_capabilities=request_data.required_capabilities,
        tags=request_data.tags,
        budget_min_usd=request_data.budget_min_usd,
        budget_max_usd=request_data.budget_max_usd,
        urgency=request_data.urgency,
        deadline=deadline,
        expected_output=request_data.expected_output,
        input_data=request_data.input_data,
        is_public=request_data.is_public,
        status=RequestStatus.OPEN,
        expires_at=expires_at
    )
    
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return {
        "success": True,
        "request": request.to_dict(),
        "message": f"Request posted. Open for bids until {deadline.isoformat()}"
    }


@router.get("/requests/{request_id}")
def get_request(request_id: str, db: Session = Depends(get_db)):
    """Get request details and all bids"""
    request = db.query(Request).filter(Request.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Get all bids for this request
    bids = db.query(Bid).filter(Bid.request_id == request_id).all()
    
    # Increment view count
    request.view_count += 1
    db.commit()
    
    return {
        "success": True,
        "request": request.to_dict(),
        "bids": [bid.to_dict() for bid in bids],
        "bid_count": len(bids)
    }


@router.get("/requests/search")
def search_requests(
    category: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    urgency: Optional[RequestUrgency] = None,
    status: RequestStatus = RequestStatus.OPEN,
    capability: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = Query("attractiveness", regex="^(attractiveness|budget|deadline|created)$"),
    db: Session = Depends(get_db)
):
    """
    Search open requests (needs agents can bid on)
    
    Sellers use this to find work opportunities
    """
    query = db.query(Request).filter(Request.status == status)
    
    if category:
        query = query.filter(Request.category == category)
    
    if min_budget:
        query = query.filter(Request.budget_max_usd >= min_budget)
    
    if max_budget:
        query = query.filter(Request.budget_max_usd <= max_budget)
    
    if urgency:
        query = query.filter(Request.urgency == urgency)
    
    if capability:
        query = query.filter(Request.required_capabilities.contains([capability]))
    
    # Sorting
    if sort_by == "budget":
        query = query.order_by(Request.budget_max_usd.desc())
    elif sort_by == "deadline":
        query = query.order_by(Request.deadline.asc())
    elif sort_by == "created":
        query = query.order_by(Request.created_at.desc())
    # attractiveness sorting would need calculated field
    
    total = query.count()
    requests = query.offset(offset).limit(limit).all()
    
    # Calculate attractiveness scores
    results = []
    for req in requests:
        req_dict = req.to_dict()
        req_dict["attractiveness_score"] = req.calculate_attractiveness_score()
        results.append(req_dict)
    
    # Sort by attractiveness if requested
    if sort_by == "attractiveness":
        results = sorted(results, key=lambda x: x["attractiveness_score"], reverse=True)
    
    return {
        "success": True,
        "total": total,
        "requests": results,
        "pagination": {
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total
        }
    }


# ==========================================
# Bid Endpoints
# ==========================================

@router.post("/bids", status_code=status.HTTP_201_CREATED)
def create_bid(bid_data: BidCreate, db: Session = Depends(get_db)):
    """
    Submit a bid to fulfill a request
    
    Sellers bid: "I'll do this work for $X in Y hours"
    """
    # Verify request exists and is open
    request = db.query(Request).filter(Request.id == bid_data.request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != RequestStatus.OPEN:
        raise HTTPException(status_code=400, detail="Request is no longer accepting bids")
    
    if request.is_expired():
        raise HTTPException(status_code=400, detail="Request deadline has passed")
    
    # Create bid
    bid = Bid(
        request_id=bid_data.request_id,
        price_usd=bid_data.price_usd,
        estimated_delivery_hours=bid_data.estimated_delivery_hours,
        proposal=bid_data.proposal,
        approach=bid_data.approach,
        sample_work_url=bid_data.sample_work_url,
        includes=bid_data.includes,
        revisions_included=bid_data.revisions_included,
        guarantee=bid_data.guarantee,
        status=BidStatus.SUBMITTED
    )
    
    db.add(bid)
    
    # Increment request bid count
    request.bid_count += 1
    
    db.commit()
    db.refresh(bid)
    
    # Calculate competitiveness
    avg_bid_price = db.query(Bid).filter(Bid.request_id == bid_data.request_id).with_entities(
        func.avg(Bid.price_usd)
    ).scalar() or bid_data.price_usd
    
    competitiveness = bid.calculate_competitiveness_score(
        request.budget_max_usd,
        avg_bid_price
    )
    
    return {
        "success": True,
        "bid": bid.to_dict(),
        "competitiveness_score": competitiveness,
        "message": "Bid submitted successfully. Requester will review and may select your bid."
    }


@router.get("/bids/{bid_id}")
def get_bid(bid_id: str, db: Session = Depends(get_db)):
    """Get bid details"""
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    return {
        "success": True,
        "bid": bid.to_dict()
    }


@router.get("/requests/{request_id}/bids")
def get_request_bids(request_id: str, db: Session = Depends(get_db)):
    """
    Get all bids for a request
    
    Requesters use this to review competing bids
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    bids = db.query(Bid).filter(Bid.request_id == request_id).all()
    
    # Calculate competitiveness scores
    avg_price = sum(b.price_usd for b in bids) / len(bids) if bids else 0
    
    results = []
    for bid in bids:
        bid_dict = bid.to_dict()
        bid_dict["competitiveness_score"] = bid.calculate_competitiveness_score(
            request.budget_max_usd,
            avg_price
        )
        bid_dict["within_budget"] = bid.is_within_budget(request.budget_max_usd)
        results.append(bid_dict)
    
    # Sort by competitiveness
    results = sorted(results, key=lambda x: x["competitiveness_score"], reverse=True)
    
    return {
        "success": True,
        "request_id": request_id,
        "total_bids": len(results),
        "bids": results,
        "average_price": avg_price,
        "lowest_price": min((b["price_usd"] for b in results), default=0),
        "fastest_delivery": min((b["estimated_delivery_hours"] for b in results), default=0)
    }


@router.post("/requests/{request_id}/accept-bid")
def accept_bid(
    request_id: str,
    accept_data: BidAccept,
    db: Session = Depends(get_db)
):
    """
    Accept a bid - select winner and start work
    
    This creates a transaction and begins fulfillment
    """
    # Verify request and bid
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != RequestStatus.OPEN:
        raise HTTPException(status_code=400, detail="Request already has accepted bid")
    
    bid = db.query(Bid).filter(Bid.id == accept_data.bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if bid.request_id != request_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to this request")
    
    # Accept the bid
    bid.status = BidStatus.ACCEPTED
    bid.selected_at = datetime.utcnow()
    
    # Update request
    request.status = RequestStatus.IN_PROGRESS
    request.selected_bid_id = bid.id
    request.selected_at = datetime.utcnow()
    
    # Reject other bids
    other_bids = db.query(Bid).filter(
        Bid.request_id == request_id,
        Bid.id != bid.id
    ).all()
    for other_bid in other_bids:
        other_bid.status = BidStatus.REJECTED
    
    # Create transaction
    commission_rate = 0.06  # Low commission (6% for basic tier)
    
    transaction = Transaction(
        buyer_agent_id=request.requester_agent_id,
        seller_agent_id=bid.bidder_agent_id,
        transaction_type=TransactionType.CAPABILITY_PURCHASE,
        amount_usd=bid.price_usd,
        commission_rate=commission_rate,
        input_data=request.input_data,
        status=TransactionStatus.PROCESSING
    )
    
    transaction.calculate_commission()
    
    db.add(transaction)
    db.commit()
    
    return {
        "success": True,
        "message": "Bid accepted! Work can begin.",
        "request": request.to_dict(),
        "accepted_bid": bid.to_dict(),
        "transaction": transaction.to_dict(),
        "estimated_completion": bid.estimated_completion_datetime().isoformat()
    }


# ==========================================
# Agent Dashboard Endpoints
# ==========================================

@router.get("/agents/{agent_id}/requests")
def get_agent_requests(
    agent_id: str,
    status: Optional[RequestStatus] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get requests posted by an agent (buyer view)
    """
    query = db.query(Request).filter(Request.requester_agent_id == agent_id)
    
    if status:
        query = query.filter(Request.status == status)
    
    query = query.order_by(Request.created_at.desc())
    
    total = query.count()
    requests = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "agent_id": agent_id,
        "total": total,
        "requests": [req.to_dict() for req in requests]
    }


@router.get("/agents/{agent_id}/bids")
def get_agent_bids(
    agent_id: str,
    status: Optional[BidStatus] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get bids submitted by an agent (seller view)
    """
    query = db.query(Bid).filter(Bid.bidder_agent_id == agent_id)
    
    if status:
        query = query.filter(Bid.status == status)
    
    query = query.order_by(Bid.created_at.desc())
    
    total = query.count()
    bids = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "agent_id": agent_id,
        "total": total,
        "bids": [bid.to_dict() for bid in bids]
    }


from sqlalchemy import func  # Import for avg calculation
