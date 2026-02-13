"""
Wallet-Based Authentication for Agents
Agents prove ownership by signing challenge with their Solana wallet
"""
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
import time
import hashlib
import base58
from solders.pubkey import Pubkey

from database.base import get_db
from models.agent import Agent

# Active challenges (in production: use Redis)
active_challenges = {}

def generate_challenge(wallet_address: str) -> dict:
    """
    Generate authentication challenge for wallet
    
    Args:
        wallet_address: Agent's Solana wallet address
        
    Returns:
        dict: {"challenge": str, "expires_at": int}
    """
    # Create challenge
    timestamp = int(time.time())
    challenge_text = f"Sign this message to authenticate with Agent Directory: {timestamp}"
    challenge_hash = hashlib.sha256(challenge_text.encode()).hexdigest()
    
    # Store challenge (expires in 60 seconds)
    active_challenges[wallet_address] = {
        "challenge": challenge_hash,
        "challenge_text": challenge_text,
        "expires_at": timestamp + 60
    }
    
    return {
        "challenge": challenge_text,
        "challenge_hash": challenge_hash,
        "expires_at": timestamp + 60
    }

def verify_signature(wallet_address: str, signature_base58: str) -> bool:
    """
    Verify agent signed the challenge with their wallet
    
    Args:
        wallet_address: Agent's wallet public key
        signature_base58: Base58-encoded signature
        
    Returns:
        bool: True if signature is valid
    """
    # Check challenge exists
    if wallet_address not in active_challenges:
        raise HTTPException(
            status_code=401, 
            detail="No active challenge for wallet. Request a new challenge."
        )
    
    challenge_data = active_challenges[wallet_address]
    
    # Check not expired
    if time.time() > challenge_data["expires_at"]:
        del active_challenges[wallet_address]
        raise HTTPException(
            status_code=401, 
            detail="Challenge expired. Request a new challenge."
        )
    
    try:
        # Verify wallet address format
        pubkey = Pubkey.from_string(wallet_address)
        
        # TODO: Proper Solana signature verification
        # For MVP, simplified verification (Phase 2: implement proper ed25519)
        # In production, use: verify_signature(pubkey, signature_bytes, message_bytes)
        
        # Simplified verification for MVP
        is_valid = len(signature_base58) > 0  # Placeholder
        
        if is_valid:
            # Remove challenge (one-time use)
            del active_challenges[wallet_address]
            return True
        else:
            raise HTTPException(
                status_code=401, 
                detail="Invalid signature"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Signature verification failed: {e}"
        )

async def verify_wallet_auth(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Agent:
    """
    FastAPI dependency for wallet-based authentication
    
    Header format: Authorization: Wallet <address>:<signature>
    
    Returns:
        Agent: Authenticated agent object
    """
    if not authorization or not authorization.startswith("Wallet "):
        raise HTTPException(
            status_code=401, 
            detail="Missing wallet authorization. Use: Authorization: Wallet <address>:<signature>"
        )
    
    auth_data = authorization.replace("Wallet ", "")
    
    if ":" not in auth_data:
        raise HTTPException(
            status_code=401, 
            detail="Invalid auth format. Expected: Wallet <address>:<signature>"
        )
    
    wallet_address, signature = auth_data.split(":", 1)
    
    # Verify signature
    if not verify_signature(wallet_address, signature):
        raise HTTPException(
            status_code=401, 
            detail="Invalid wallet signature"
        )
    
    # Get agent from database
    agent = db.query(Agent).filter(Agent.wallet_address == wallet_address).first()
    
    if not agent:
        raise HTTPException(
            status_code=404, 
            detail="Agent not found for this wallet address"
        )
    
    if not agent.is_active:
        raise HTTPException(
            status_code=403, 
            detail="Agent account is inactive"
        )
    
    return agent

# Simplified auth for testing (just wallet address, no signature)
async def verify_wallet_simple(
    wallet_address: str = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
) -> Agent:
    """
    Simplified wallet auth for testing (no signature verification)
    Use this during development, replace with verify_wallet_auth in production
    """
    if not wallet_address:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Wallet-Address header"
        )
    
    agent = db.query(Agent).filter(Agent.wallet_address == wallet_address).first()
    
    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found for this wallet address"
        )
    
    return agent
