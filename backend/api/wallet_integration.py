"""
Wallet Integration for Agent Directory
Auto-create Solana wallets on agent registration
"""
import sys
import os

# Add payments directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'payments'))

from solana_wallet import SolanaWalletManager
from datetime import datetime

# Initialize wallet manager
wallet_manager = SolanaWalletManager()

def create_agent_wallet():
    """
    Generate new Solana wallet for agent
    
    Returns:
        dict: {
            "wallet_address": str,
            "wallet_private_key_encrypted": str,
            "usdc_address": str
        }
    """
    wallet = wallet_manager.generate_agent_wallet()
    
    return {
        "wallet_address": wallet["public_key"],
        "wallet_private_key_encrypted": wallet["private_key_encrypted"],
        "usdc_address": wallet["usdc_address"],
        "wallet_created_at": datetime.utcnow()
    }

def get_agent_balance(wallet_address: str) -> float:
    """
    Get USDC balance for agent wallet
    
    Args:
        wallet_address: Agent's Solana public key
        
    Returns:
        float: USDC balance
    """
    try:
        balance = wallet_manager.get_balance(wallet_address)
        return balance
    except Exception as e:
        print(f"Error getting balance for {wallet_address}: {e}")
        return 0.0

def validate_wallet_address(address: str) -> bool:
    """
    Validate Solana address format
    
    Args:
        address: Public key to validate
        
    Returns:
        bool: True if valid
    """
    return wallet_manager.validate_address(address)
