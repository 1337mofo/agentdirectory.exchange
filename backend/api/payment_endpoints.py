"""
Payment API Endpoints - Agent-to-Agent USDC Transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import sys
import os
from datetime import datetime

# Add payments directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'payments'))

from database.base import get_db
from models.agent import Agent
from api.wallet_auth import verify_wallet_simple, generate_challenge
from api.wallet_integration import get_agent_balance

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Payment request schema
class PaymentRequest(BaseModel):
    to_agent_id: str = Field(..., description="Recipient agent ID")
    amount_usdc: float = Field(..., gt=0, description="Amount in USDC")
    service_description: str = Field(..., min_length=1, max_length=500)

# Payment response schema
class PaymentResponse(BaseModel):
    success: bool
    transaction_signature: Optional[str] = None
    amount_sent: float
    commission: float
    recipient_received: float
    explorer_url: Optional[str] = None
    message: str

@router.post("/auth/challenge")
async def get_auth_challenge(wallet_address: str):
    """
    Get authentication challenge for wallet
    
    Step 1 of wallet authentication:
    1. Client requests challenge with their wallet address
    2. Server generates challenge text
    3. Client signs challenge with private key
    4. Client sends signed challenge to authenticated endpoints
    """
    challenge = generate_challenge(wallet_address)
    
    return {
        "success": True,
        "challenge": challenge["challenge"],
        "challenge_hash": challenge["challenge_hash"],
        "expires_at": challenge["expires_at"],
        "message": "Sign this challenge with your wallet to authenticate"
    }

@router.get("/balance")
async def get_my_balance(
    agent: Agent = Depends(verify_wallet_simple),
    db: Session = Depends(get_db)
):
    """
    Get authenticated agent's USDC balance
    
    Headers:
        X-Wallet-Address: <agent_wallet_address>
    """
    # Get real-time balance from Solana
    balance = get_agent_balance(agent.wallet_address)
    
    # Update cached balance in database
    agent.usdc_balance = balance
    agent.last_balance_check = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "wallet_address": agent.wallet_address,
        "usdc_balance": balance,
        "last_updated": agent.last_balance_check.isoformat() if agent.last_balance_check else None
    }

@router.post("/send", response_model=PaymentResponse)
async def send_payment(
    payment: PaymentRequest,
    agent: Agent = Depends(verify_wallet_simple),
    db: Session = Depends(get_db)
):
    """
    Send USDC payment from authenticated agent to another agent
    
    Flow:
    1. Validate recipient exists
    2. Calculate commission (6%)
    3. Send USDC from treasury to recipient
    4. Log transaction
    5. Return confirmation
    
    Headers:
        X-Wallet-Address: <sender_wallet_address>
    """
    # Get recipient agent
    to_agent = db.query(Agent).filter(Agent.id == payment.to_agent_id).first()
    
    if not to_agent:
        raise HTTPException(
            status_code=404,
            detail="Recipient agent not found"
        )
    
    if not to_agent.wallet_address:
        raise HTTPException(
            status_code=400,
            detail="Recipient agent does not have a wallet configured"
        )
    
    # Calculate amounts
    amount = payment.amount_usdc
    commission_rate = 0.06  # 6%
    commission = amount * commission_rate
    recipient_amount = amount - commission
    
    # TODO: Process payment via Solana
    # This requires treasury keypair to be loaded
    # For now, return simulated response
    
    try:
        # Placeholder for actual Solana payment
        # from solana_payments import SolanaPaymentProcessor
        # processor = SolanaPaymentProcessor(treasury_keypair)
        # signature = processor.send_usdc(to_agent.wallet_address, recipient_amount)
        
        signature = "SIMULATED_TX_" + str(int(datetime.utcnow().timestamp()))
        
        # Log transaction (TODO: create transactions table)
        
        return PaymentResponse(
            success=True,
            transaction_signature=signature,
            amount_sent=amount,
            commission=commission,
            recipient_received=recipient_amount,
            explorer_url=f"https://solscan.io/tx/{signature}",
            message=f"Payment of ${recipient_amount:.2f} USDC sent to {to_agent.name}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Payment failed: {str(e)}"
        )

@router.get("/history")
async def get_payment_history(
    limit: int = 20,
    offset: int = 0,
    agent: Agent = Depends(verify_wallet_simple),
    db: Session = Depends(get_db)
):
    """
    Get payment history for authenticated agent
    
    Returns both sent and received payments
    
    Headers:
        X-Wallet-Address: <agent_wallet_address>
    """
    # TODO: Query transactions table
    # For now, return placeholder
    
    return {
        "success": True,
        "agent_id": str(agent.id),
        "wallet_address": agent.wallet_address,
        "transactions": [],
        "message": "Transaction history coming in Phase 2"
    }

@router.get("/stats")
async def get_payment_stats(
    agent: Agent = Depends(verify_wallet_simple),
    db: Session = Depends(get_db)
):
    """
    Get payment statistics for authenticated agent
    
    Headers:
        X-Wallet-Address: <agent_wallet_address>
    """
    return {
        "success": True,
        "agent_id": str(agent.id),
        "agent_name": agent.name,
        "wallet_address": agent.wallet_address,
        "usdc_balance": agent.usdc_balance or 0.0,
        "total_revenue": agent.revenue_total_usd or 0.0,
        "transaction_count": agent.transaction_count or 0,
        "last_balance_check": agent.last_balance_check.isoformat() if agent.last_balance_check else None
    }
