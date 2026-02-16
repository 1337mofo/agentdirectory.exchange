"""
Test Solana Payment Flow on Devnet
Tests wallet generation, treasury funding check, and USDC transfer
"""
from solana_payments import SolanaPaymentProcessor
from solana_wallet import SolanaWalletManager
from solders.keypair import Keypair
import base58
import json
import sys

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 70)
    print("SOLANA DEVNET PAYMENT TEST")
    print("=" * 70)
    
    # Load treasury
    print("\n[1] Loading treasury wallet...")
    try:
        with open("TREASURY_WALLET_DEVNET.json") as f:
            treasury_data = json.load(f)
        
        treasury_keypair = Keypair.from_bytes(
            base58.b58decode(treasury_data["private_key"])
        )
        
        print(f"   Treasury: {treasury_data['public_key']}")
        
    except FileNotFoundError:
        print("   ERROR: TREASURY_WALLET_DEVNET.json not found")
        print("   Run: python generate_treasury.py devnet")
        return
    
    # Initialize processor (devnet)
    print("\n[2] Connecting to Solana devnet...")
    processor = SolanaPaymentProcessor(
        treasury_keypair=treasury_keypair,
        rpc_url="https://api.devnet.solana.com"
    )
    print("   Connected [OK]")
    
    # Check treasury balance
    print("\n[3] Checking treasury balance...")
    balance = processor.get_treasury_balance()
    print(f"   Balance: ${balance:.2f} USDC")
    
    if balance == 0:
        print("\n   [WARN]  Treasury needs funding!")
        print(f"\n   INSTRUCTIONS:")
        print(f"   1. Get test SOL (for gas):")
        print(f"      solana airdrop 2 {treasury_data['public_key']} --url devnet")
        print(f"\n   2. Get test USDC:")
        print(f"      Visit: https://spl-token-faucet.com/?token-name=USDC")
        print(f"      Enter: {treasury_data['public_key']}")
        print(f"\n   3. Run this script again")
        return
    
    # Generate recipient wallet
    print("\n[4] Generating recipient wallet...")
    manager = SolanaWalletManager(rpc_url="https://api.devnet.solana.com")
    recipient = manager.generate_agent_wallet()
    print(f"   Recipient: {recipient['public_key'][:8]}...{recipient['public_key'][-8:]}")
    
    # Send test payment
    print("\n[5] Sending test payment (0.10 USDC)...")
    try:
        signature = processor.send_usdc(
            to_address=recipient['public_key'],
            amount_usdc=0.10,
            memo="Test payment - devnet"
        )
        
        print(f"   [OK] Payment sent!")
        print(f"   Signature: {signature[:8]}...{signature[-8:]}")
        print(f"\n   View on Solscan:")
        print(f"   https://solscan.io/tx/{signature}?cluster=devnet")
        
        # Verify transaction
        print("\n[6] Verifying transaction...")
        confirmed = processor.verify_transaction(signature, max_wait_seconds=30)
        
        if confirmed:
            print("   [OK] Transaction confirmed on-chain!")
        else:
            print("   [WARN]  Transaction not confirmed (may still be pending)")
        
        # Check recipient balance
        print("\n[7] Checking recipient balance...")
        recipient_balance = manager.get_balance(recipient['public_key'])
        print(f"   Recipient balance: ${recipient_balance:.2f} USDC")
        
        if recipient_balance > 0:
            print("\n   [OK] PAYMENT FLOW WORKS!")
        else:
            print("\n   [WARN]  Payment sent but balance not updated yet (wait a few seconds)")
        
    except Exception as e:
        print(f"   ✗ Payment failed: {e}")
        return
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Integrate with Agent Directory API")
    print("2. Test agent-to-agent payment")
    print("3. Deploy to production")
    print()

if __name__ == "__main__":
    main()
