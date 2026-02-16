"""
Generate Treasury Wallet for Agent Directory Exchange
ONE-TIME SETUP - Creates secure Solana wallet for exchange treasury
"""
from solders.keypair import Keypair
import base58
import json
import sys
from datetime import datetime

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def generate_treasury_wallet(network="devnet"):
    """
    Generate new Solana wallet for treasury
    
    Args:
        network: "devnet" or "mainnet"
    
    Returns:
        dict: Treasury wallet data
    """
    print("=" * 70)
    print("TREASURY WALLET GENERATOR")
    print("=" * 70)
    print(f"\nNetwork: {network}")
    print("Generating secure Solana keypair...\n")
    
    # Generate keypair
    treasury = Keypair()
    
    # Extract keys
    public_key = str(treasury.pubkey())
    private_key_bytes = bytes(treasury)
    private_key_base58 = base58.b58encode(private_key_bytes).decode()
    
    # Prepare data
    treasury_data = {
        "public_key": public_key,
        "private_key": private_key_base58,
        "network": network,
        "created_at": datetime.utcnow().isoformat(),
        "description": "Agent Directory Exchange Treasury Wallet"
    }
    
    # Display info
    print("[OK] Treasury Wallet Generated\n")
    print(f"Public Key (Wallet Address):")
    print(f"  {public_key}\n")
    print(f"Private Key (BASE58):")
    print(f"  {private_key_base58[:30]}... [REDACTED]\n")
    
    # Save to file
    filename = f"TREASURY_WALLET_{network.upper()}.json"
    with open(filename, "w") as f:
        json.dump(treasury_data, f, indent=2)
    
    print(f"💾 Saved to: {filename}\n")
    
    # Security warnings
    print("=" * 70)
    print("🔒 SECURITY WARNINGS")
    print("=" * 70)
    print("1. KEEP THIS FILE SECURE - Do NOT commit to git")
    print("2. BACKUP this file to secure location (password manager)")
    print("3. DO NOT share private key with anyone")
    print("4. Add to .gitignore immediately")
    print("5. Consider hardware wallet for mainnet (>$10K)")
    print("=" * 70)
    
    # Next steps
    print("\n📋 NEXT STEPS:\n")
    if network == "devnet":
        print("1. Fund wallet with test SOL:")
        print(f"   solana airdrop 2 {public_key} --url devnet\n")
        print("2. Get test USDC:")
        print(f"   Visit: https://spl-token-faucet.com/?token-name=USDC")
        print(f"   Enter wallet: {public_key}\n")
        print("3. Test payment:")
        print(f"   python test_devnet_payment.py\n")
    else:
        print("1. Buy USDC on exchange (Coinbase/Kraken)")
        print(f"2. Send USDC to: {public_key}")
        print("3. Verify balance:")
        print("   python check_treasury_balance.py")
        print("4. Set environment variables in Railway")
        print("5. Deploy to production\n")
    
    print("=" * 70)
    
    return treasury_data

if __name__ == "__main__":
    # Check command line argument
    network = "devnet"
    if len(sys.argv) > 1:
        network = sys.argv[1].lower()
        if network not in ["devnet", "mainnet"]:
            print("[ERROR] Invalid network. Use 'devnet' or 'mainnet'")
            sys.exit(1)
    
    # Generate wallet
    treasury_data = generate_treasury_wallet(network=network)
    
    print("\n[OK] Treasury wallet ready!")
    print(f"📄 View file: TREASURY_WALLET_{network.upper()}.json\n")
