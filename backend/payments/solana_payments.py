"""
Solana USDC Payment Processor
Handles USDC transfers between exchange treasury and agent wallets
"""

from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solders.hash import Hash
from anchorpy import Provider
import base58
import os
import time

# Configuration
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDC_DECIMALS = 6

class SolanaPaymentProcessor:
    """Process USDC payments on Solana"""
    
    def __init__(self, treasury_keypair: Keypair = None, rpc_url=SOLANA_RPC_URL):
        self.client = Client(rpc_url)
        self.treasury = treasury_keypair
        self.usdc_mint = Pubkey.from_string(USDC_MINT)
        
    def send_usdc(self, to_address: str, amount_usdc: float, memo: str = None):
        """
        Send USDC from treasury to agent wallet
        
        Args:
            to_address: Recipient Solana wallet address
            amount_usdc: Amount in USDC (e.g., 0.47 for 47 cents)
            memo: Optional transaction memo
            
        Returns:
            str: Transaction signature
        """
        if not self.treasury:
            raise ValueError("Treasury keypair not initialized")
        
        try:
            # Convert USDC to base units (6 decimals)
            amount_base = int(amount_usdc * 1_000_000)
            
            # Get token accounts
            treasury_pubkey = self.treasury.pubkey()
            to_pubkey = Pubkey.from_string(to_address)
            
            treasury_usdc = get_associated_token_address(treasury_pubkey, self.usdc_mint)
            recipient_usdc = get_associated_token_address(to_pubkey, self.usdc_mint)
            
            # Build transfer instruction
            transfer_instruction = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=treasury_usdc,
                    mint=self.usdc_mint,
                    dest=recipient_usdc,
                    owner=treasury_pubkey,
                    amount=amount_base,
                    decimals=USDC_DECIMALS,
                )
            )
            
            # Get recent blockhash
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            
            # Build transaction
            transaction = Transaction()
            transaction.recent_blockhash = recent_blockhash
            transaction.fee_payer = treasury_pubkey
            transaction.add(transfer_instruction)
            
            # Sign and send
            transaction.sign(self.treasury)
            
            response = self.client.send_transaction(
                transaction,
                self.treasury,
                opts={"skip_preflight": False, "preflight_commitment": "confirmed"}
            )
            
            signature = response.value
            
            print(f"[PAYMENT] Sent ${amount_usdc:.2f} USDC to {to_address[:8]}...")
            print(f"[TX] https://solscan.io/tx/{signature}")
            
            return str(signature)
            
        except Exception as e:
            print(f"[ERROR] Payment failed: {e}")
            raise
    
    def get_treasury_balance(self):
        """Get current USDC balance in treasury"""
        if not self.treasury:
            return 0.0
        
        try:
            treasury_pubkey = self.treasury.pubkey()
            treasury_usdc = get_associated_token_address(treasury_pubkey, self.usdc_mint)
            
            response = self.client.get_token_account_balance(treasury_usdc)
            
            if response.value:
                balance = int(response.value.amount) / 1_000_000
                return balance
            return 0.0
        except Exception as e:
            print(f"[ERROR] Failed to get treasury balance: {e}")
            return 0.0
    
    def verify_transaction(self, signature: str, max_wait_seconds: int = 30):
        """
        Verify transaction was confirmed on-chain
        
        Args:
            signature: Transaction signature to verify
            max_wait_seconds: Maximum time to wait for confirmation
            
        Returns:
            bool: True if confirmed
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = self.client.get_signature_statuses([signature])
                
                if response.value and response.value[0]:
                    status = response.value[0]
                    if status.confirmation_status in ["confirmed", "finalized"]:
                        print(f"[TX] Confirmed: {signature[:8]}...")
                        return True
                
                time.sleep(1)  # Wait 1 second before retry
            except Exception as e:
                print(f"[ERROR] Verification check failed: {e}")
                time.sleep(1)
        
        print(f"[ERROR] Transaction not confirmed within {max_wait_seconds}s")
        return False
    
    def batch_send(self, payments: list):
        """
        Send multiple USDC payments in batch
        
        Args:
            payments: List of {"to": address, "amount": usdc_amount} dicts
            
        Returns:
            list: Transaction signatures
        """
        signatures = []
        
        for payment in payments:
            try:
                sig = self.send_usdc(
                    to_address=payment["to"],
                    amount_usdc=payment["amount"],
                    memo=payment.get("memo")
                )
                signatures.append(sig)
            except Exception as e:
                print(f"[ERROR] Batch payment failed: {e}")
                signatures.append(None)
        
        return signatures


# Transaction record for database
class TransactionRecord:
    """Database model for Solana transactions"""
    
    def __init__(self, signature, from_address, to_address, amount_usdc, commission_usdc, memo=None):
        self.signature = signature
        self.from_address = from_address
        self.to_address = to_address
        self.amount_usdc = amount_usdc
        self.commission_usdc = commission_usdc
        self.memo = memo
        self.timestamp = time.time()
        self.confirmed = False
    
    def to_dict(self):
        return {
            "signature": self.signature,
            "from": self.from_address,
            "to": self.to_address,
            "amount": self.amount_usdc,
            "commission": self.commission_usdc,
            "memo": self.memo,
            "timestamp": self.timestamp,
            "confirmed": self.confirmed,
            "explorer_url": f"https://solscan.io/tx/{self.signature}"
        }


# Testing
if __name__ == "__main__":
    print("="*60)
    print("SOLANA PAYMENT PROCESSOR - TEST")
    print("="*60)
    
    print("\n[WARNING] This is test mode")
    print("[INFO] To process real payments, set TREASURY_PRIVATE_KEY")
    
    # In production, treasury keypair would be loaded from secure storage
    # treasury_keypair = Keypair.from_bytes(encrypted_key)
    
    processor = SolanaPaymentProcessor()
    
    print(f"\n[RPC] Connected to: {SOLANA_RPC_URL}")
    print(f"[USDC] Mint: {USDC_MINT}")
    
    print("\n[OK] Payment processor initialized")
    print("="*60)
