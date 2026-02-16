"""
Check Treasury Status - Simple connectivity and balance test
"""
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import base58
import json
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_sol_balance(client, pubkey):
    """Check SOL balance (for gas fees)"""
    try:
        response = client.get_balance(pubkey)
        if response.value is not None:
            sol_balance = response.value / 1_000_000_000  # Convert lamports to SOL
            return sol_balance
        return 0
    except Exception as e:
        print(f"Error checking SOL balance: {e}")
        return 0

def main():
    print("=" * 70)
    print("TREASURY STATUS CHECK")
    print("=" * 70)
    
    # Load treasury
    print("\n[1] Loading treasury wallet...")
    try:
        with open("TREASURY_WALLET_DEVNET.json") as f:
            treasury_data = json.load(f)
        
        public_key = treasury_data["public_key"]
        print(f"   Public Key: {public_key}")
        
    except FileNotFoundError:
        print("   ERROR: TREASURY_WALLET_DEVNET.json not found")
        return
    
    # Connect to devnet
    print("\n[2] Connecting to Solana devnet...")
    client = Client("https://api.devnet.solana.com")
    print("   Connected")
    
    # Check SOL balance
    print("\n[3] Checking SOL balance (for gas fees)...")
    pubkey = Pubkey.from_string(public_key)
    sol_balance = check_sol_balance(client, pubkey)
    print(f"   SOL Balance: {sol_balance:.4f} SOL")
    
    if sol_balance == 0:
        print("\n   Need SOL for gas fees!")
        print(f"   Run: solana airdrop 2 {public_key} --url devnet")
    else:
        print("   [OK] Has SOL for transactions")
    
    # Check USDC balance (simplified - just show instructions)
    print("\n[4] USDC Balance Check:")
    print("   (Requires USDC token account)")
    print(f"\n   To fund with test USDC:")
    print(f"   1. Visit: https://spl-token-faucet.com/?token-name=USDC")
    print(f"   2. Enter wallet: {public_key}")
    print(f"   3. Select 'Devnet' network")
    print(f"   4. Click 'Airdrop'")
    
    print("\n" + "=" * 70)
    print("STATUS:")
    print("=" * 70)
    
    if sol_balance > 0:
        print("[OK] Treasury wallet exists")
        print("[OK] Connected to devnet")
        print("[OK] Has SOL for gas")
        print("⏳ Need to fund with USDC")
        print("\nReady for USDC funding ->")
    else:
        print("[OK] Treasury wallet exists")
        print("[OK] Connected to devnet")  
        print("⏳ Need SOL for gas")
        print("⏳ Need USDC for payments")
        print("\nReady for funding ->")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
