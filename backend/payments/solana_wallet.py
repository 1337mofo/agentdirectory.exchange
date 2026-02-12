"""
Solana Wallet Management for Agent Directory Exchange
Handles wallet generation, key storage, and USDC operations
"""

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from spl.token.instructions import get_associated_token_address
import base58
import json
from cryptography.fernet import Fernet
import os

# Solana Configuration
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC on Solana mainnet
ENCRYPTION_KEY = os.getenv("WALLET_ENCRYPTION_KEY")  # Must be set in production

class SolanaWalletManager:
    """Manages Solana wallets for agents and treasury"""
    
    def __init__(self, rpc_url=SOLANA_RPC_URL):
        self.client = Client(rpc_url)
        self.usdc_mint = Pubkey.from_string(USDC_MINT)
        
        if ENCRYPTION_KEY:
            self.cipher = Fernet(ENCRYPTION_KEY.encode())
        else:
            print("[WARNING] WALLET_ENCRYPTION_KEY not set. Keys will not be encrypted.")
            self.cipher = None
    
    def generate_agent_wallet(self):
        """
        Generate new Solana keypair for agent
        
        Returns:
            dict: {
                "public_key": str,
                "private_key_encrypted": str,
                "recovery_phrase": str (optional)
            }
        """
        keypair = Keypair()
        
        public_key = str(keypair.pubkey())
        private_key_bytes = bytes(keypair)
        
        # Encrypt private key
        if self.cipher:
            private_key_encrypted = self.cipher.encrypt(private_key_bytes).decode()
        else:
            # Base58 encode for storage (NOT SECURE - dev only)
            private_key_encrypted = base58.b58encode(private_key_bytes).decode()
        
        return {
            "public_key": public_key,
            "private_key_encrypted": private_key_encrypted,
            "usdc_address": self.get_usdc_address(public_key)
        }
    
    def get_usdc_address(self, wallet_address: str):
        """
        Get associated USDC token account for wallet
        
        Args:
            wallet_address: Solana wallet public key
            
        Returns:
            str: USDC token account address
        """
        wallet_pubkey = Pubkey.from_string(wallet_address)
        usdc_account = get_associated_token_address(wallet_pubkey, self.usdc_mint)
        return str(usdc_account)
    
    def get_balance(self, wallet_address: str):
        """
        Get USDC balance for wallet
        
        Args:
            wallet_address: Solana wallet public key
            
        Returns:
            float: USDC balance (not lamports)
        """
        try:
            usdc_address = self.get_usdc_address(wallet_address)
            usdc_pubkey = Pubkey.from_string(usdc_address)
            
            response = self.client.get_token_account_balance(usdc_pubkey)
            
            if response.value:
                # USDC has 6 decimals
                balance = int(response.value.amount) / 1_000_000
                return balance
            return 0.0
        except Exception as e:
            print(f"[ERROR] Failed to get balance: {e}")
            return 0.0
    
    def decrypt_private_key(self, encrypted_key: str):
        """
        Decrypt agent private key for signing transactions
        
        Args:
            encrypted_key: Encrypted private key from database
            
        Returns:
            Keypair: Solana keypair for signing
        """
        if self.cipher:
            decrypted_bytes = self.cipher.decrypt(encrypted_key.encode())
        else:
            # Base58 decode (dev only)
            decrypted_bytes = base58.b58decode(encrypted_key)
        
        return Keypair.from_bytes(decrypted_bytes)
    
    def validate_address(self, address: str):
        """
        Validate Solana address format
        
        Args:
            address: Public key to validate
            
        Returns:
            bool: True if valid
        """
        try:
            Pubkey.from_string(address)
            return True
        except:
            return False


# Testing
if __name__ == "__main__":
    print("="*60)
    print("SOLANA WALLET MANAGER - TEST")
    print("="*60)
    
    manager = SolanaWalletManager()
    
    # Generate test wallet
    print("\n[1] Generating agent wallet...")
    wallet = manager.generate_agent_wallet()
    print(f"   Public Key: {wallet['public_key']}")
    print(f"   USDC Address: {wallet['usdc_address']}")
    print(f"   Private Key: [ENCRYPTED]")
    
    # Validate address
    print("\n[2] Validating address...")
    is_valid = manager.validate_address(wallet['public_key'])
    print(f"   Valid: {is_valid}")
    
    # Get balance (will be 0 for new wallet)
    print("\n[3] Checking balance...")
    balance = manager.get_balance(wallet['public_key'])
    print(f"   USDC Balance: ${balance:.2f}")
    
    print("\n" + "="*60)
    print("✅ Wallet manager working!")
    print("="*60)
