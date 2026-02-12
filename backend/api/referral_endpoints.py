"""
Referral API Endpoints - Agent referral program
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database.base import get_db
from models.agent import Agent
from models.referral import Referral, ReferralPayout, ReferralStatus
from models.transaction import Transaction

router = APIRouter(prefix="/api/v1", tags=["Referrals"])


# ==========================================
# Request Schemas
# ==========================================

class ReferralCodeCreate(BaseModel):
    """Generate referral code for an agent"""
    agent_id: str


class ReferralSignup(BaseModel):
    """Sign up using referral code"""
    agent_id: str
    referral_code: str


# ==========================================
# Referral Code Endpoints
# ==========================================

@router.post("/agents/{agent_id}/referral-code", status_code=status.HTTP_201_CREATED)
def generate_referral_code(agent_id: str, db: Session = Depends(get_db)):
    """
    Generate unique referral code for an agent
    
    Agent can share this code with other agents to earn referral commission
    """
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent already has referral code
    existing = db.query(Referral).filter(
        Referral.referrer_agent_id == agent_id,
        Referral.referee_agent_id == None
    ).first()
    
    if existing:
        return {
            "success": True,
            "referral_code": existing.referral_code,
            "message": "Existing referral code returned",
            "share_url": f"https://agent.exchange/signup?ref={existing.referral_code}"
        }
    
    # Generate new referral code
    referral_code = Referral.generate_referral_code()
    
    referral = Referral(
        referral_code=referral_code,
        referrer_agent_id=agent_id,
        status=ReferralStatus.PENDING
    )
    
    db.add(referral)
    db.commit()
    db.refresh(referral)
    
    return {
        "success": True,
        "referral_code": referral_code,
        "commission_rate": "2%",
        "referee_benefit": "1% discount (5% commission instead of 6%)",
        "share_url": f"https://agent.exchange/signup?ref={referral_code}",
        "message": "Share this code with other agents to earn 2% commission on their sales"
    }


@router.get("/agents/{agent_id}/referral-code")
def get_referral_code(agent_id: str, db: Session = Depends(get_db)):
    """Get agent's referral code"""
    referral = db.query(Referral).filter(
        Referral.referrer_agent_id == agent_id,
        Referral.referee_agent_id == None
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=404,
            detail="No referral code found. Generate one first."
        )
    
    return {
        "success": True,
        "referral_code": referral.referral_code,
        "share_url": f"https://agent.exchange/signup?ref={referral.referral_code}"
    }


# ==========================================
# Referral Signup
# ==========================================

@router.post("/referrals/apply")
def apply_referral_code(signup_data: ReferralSignup, db: Session = Depends(get_db)):
    """
    Apply referral code during agent signup
    
    Links new agent to referrer for commission tracking
    """
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == signup_data.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent already has a referrer
    existing_referral = db.query(Referral).filter(
        Referral.referee_agent_id == signup_data.agent_id
    ).first()
    
    if existing_referral:
        raise HTTPException(
            status_code=400,
            detail="Agent already registered with a referral code"
        )
    
    # Find referral code template
    referral_template = db.query(Referral).filter(
        Referral.referral_code == signup_data.referral_code,
        Referral.referee_agent_id == None
    ).first()
    
    if not referral_template:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    # Create referral relationship
    referral = Referral(
        referral_code=referral_template.referral_code,
        referrer_agent_id=referral_template.referrer_agent_id,
        referee_agent_id=signup_data.agent_id,
        status=ReferralStatus.PENDING,
        referral_commission_rate=0.02,  # 2% for referrer
        referee_discount_rate=0.01  # 1% discount for referee
    )
    
    db.add(referral)
    db.commit()
    db.refresh(referral)
    
    return {
        "success": True,
        "message": "Referral code applied successfully!",
        "benefits": {
            "your_commission": "5% (1% discount from standard 6%)",
            "referrer_earns": "2% commission on your sales"
        },
        "referral": referral.to_dict()
    }


# ==========================================
# Referral Stats & Earnings
# ==========================================

@router.get("/agents/{agent_id}/referrals")
def get_agent_referrals(agent_id: str, db: Session = Depends(get_db)):
    """
    Get all agents referred by this agent
    
    Shows referral earnings and performance
    """
    referrals = db.query(Referral).filter(
        Referral.referrer_agent_id == agent_id,
        Referral.referee_agent_id != None
    ).all()
    
    # Calculate totals
    total_earnings = sum(r.total_earnings_usd for r in referrals)
    total_referees = len(referrals)
    active_referees = len([r for r in referrals if r.status == ReferralStatus.ACTIVE])
    
    return {
        "success": True,
        "agent_id": agent_id,
        "summary": {
            "total_referees": total_referees,
            "active_referees": active_referees,
            "total_earnings_usd": total_earnings,
            "average_earnings_per_referee": total_earnings / total_referees if total_referees > 0 else 0
        },
        "referrals": [r.to_dict() for r in referrals]
    }


@router.get("/agents/{agent_id}/referral-earnings")
def get_referral_earnings(agent_id: str, db: Session = Depends(get_db)):
    """
    Get detailed referral earnings history
    """
    payouts = db.query(ReferralPayout).filter(
        ReferralPayout.referrer_agent_id == agent_id
    ).order_by(ReferralPayout.created_at.desc()).all()
    
    # Calculate totals
    total_earned = sum(p.commission_amount_usd for p in payouts)
    total_paid = sum(p.commission_amount_usd for p in payouts if p.paid_out)
    pending_payout = total_earned - total_paid
    
    return {
        "success": True,
        "summary": {
            "total_earned_usd": total_earned,
            "total_paid_usd": total_paid,
            "pending_payout_usd": pending_payout,
            "total_transactions": len(payouts)
        },
        "recent_earnings": [p.to_dict() for p in payouts[:20]]
    }


# ==========================================
# Transaction Hook (Internal)
# ==========================================

def process_referral_commission(transaction: Transaction, db: Session):
    """
    Process referral commission when transaction completes
    
    Called internally by transaction completion handler
    """
    # Check if seller has a referrer
    referral = db.query(Referral).filter(
        Referral.referee_agent_id == transaction.seller_agent_id,
        Referral.status == ReferralStatus.ACTIVE
    ).first()
    
    if not referral:
        # Activate if this is first transaction
        referral = db.query(Referral).filter(
            Referral.referee_agent_id == transaction.seller_agent_id,
            Referral.status == ReferralStatus.PENDING
        ).first()
        
        if referral:
            referral.status = ReferralStatus.ACTIVE
            referral.activated_at = datetime.utcnow()
            referral.first_transaction_id = transaction.id
    
    if referral:
        # Calculate commission
        commission_breakdown = referral.calculate_commission(transaction.amount_usd)
        
        # Create payout record
        payout = ReferralPayout(
            referral_id=referral.id,
            referrer_agent_id=referral.referrer_agent_id,
            transaction_id=transaction.id,
            transaction_amount_usd=transaction.amount_usd,
            commission_amount_usd=commission_breakdown['referrer_commission'],
            commission_rate=referral.referral_commission_rate,
            paid_out=False
        )
        
        db.add(payout)
        
        # Update referral totals
        referral.total_earnings_usd += commission_breakdown['referrer_commission']
        referral.total_transactions += 1
        referral.referee_total_sales_usd += transaction.amount_usd
        
        db.commit()
        
        return {
            "referral_commission_paid": True,
            "referrer_earns": commission_breakdown['referrer_commission'],
            "referee_discount": commission_breakdown['referee_discount']
        }
    
    return {"referral_commission_paid": False}


# ==========================================
# Referral Leaderboard
# ==========================================

@router.get("/referrals/leaderboard")
def get_referral_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top referrers by earnings
    
    Public leaderboard to incentivize referrals
    """
    from sqlalchemy import func
    
    top_referrers = db.query(
        Referral.referrer_agent_id,
        func.sum(Referral.total_earnings_usd).label('total_earnings'),
        func.count(Referral.id).label('total_referrals'),
        func.count(Referral.id).filter(Referral.status == ReferralStatus.ACTIVE).label('active_referrals')
    ).filter(
        Referral.referee_agent_id != None
    ).group_by(
        Referral.referrer_agent_id
    ).order_by(
        func.sum(Referral.total_earnings_usd).desc()
    ).limit(limit).all()
    
    # Get agent names
    leaderboard = []
    for referrer_id, earnings, total, active in top_referrers:
        agent = db.query(Agent).filter(Agent.id == referrer_id).first()
        leaderboard.append({
            "rank": len(leaderboard) + 1,
            "agent_id": str(referrer_id),
            "agent_name": agent.name if agent else "Unknown",
            "total_earnings_usd": float(earnings or 0),
            "total_referrals": int(total or 0),
            "active_referrals": int(active or 0)
        })
    
    return {
        "success": True,
        "leaderboard": leaderboard
    }
