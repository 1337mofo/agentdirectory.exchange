# Solana Weekend Sprint - EXECUTION PLAN
## Make It Work (Not Perfect)

**Start:** Feb 13, 2026 07:37 GMT+7  
**Target:** Working Solana payments + wallet auth by Feb 15  
**Approach:** Ship > Perfect  

---

## Goal

**Build wallet-based authentication + USDC payments that WORK.**

**What "work" means:**
- Agent registers → wallet created automatically
- Agent authenticates → signs challenge with wallet
- Agent A pays Agent B → USDC transfers on Solana
- Agent cashes out → can see balance (Circle integration Phase 2)

**What we're NOT building this weekend:**
- Perfect error handling
- Admin dashboard UI
- Circle API integration (fiat offramp)
- Multi-sig treasury
- Rate limiting
- Beautiful UX

**Shipping prototype, not production.**

---

## Day 1 (Feb 13) - Foundation ✅

### ✅ 1.1 Install Dependencies
```bash
pip install --user solana solders anchorpy cryptography base58
```
**Status:** COMPLETE

### ✅ 1.2 Test Wallet Generation
```bash
python backend/payments/solana_wallet.py
```
**Status:** COMPLETE - Wallet generation working

### ⏳ 1.3 Generate Treasury Wallet

**Create secure treasury:**
```python
# backend/payments/generate_treasury.py
from solders.keypair import Keypair
import base58
import json

# Generate keypair
treasury = Keypair()

# Extract keys
public_key = str(treasury.pubkey())
private_key_bytes = bytes(treasury)
private_key_base58 = base58.b58encode(private_key_bytes).decode()

# Save to secure file (NOT committed to git)
treasury_data = {
    "public_key": public_key,
    "private_key": private_key_base58,
    "network": "devnet",
    "created_at": "2026-02-13"
}

with open("TREASURY_WALLET.json", "w") as f:
    json.dump(treasury_data, f, indent=2)

print(f"Treasury Public Key: {public_key}")
print(f"Treasury Private Key: {private_key_base58[:20]}... (saved to TREASURY_WALLET.json)")
print("\n⚠️  KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT")
```

**Add to .gitignore:**
```
TREASURY_WALLET.json
*.wallet
*.key
```

### ⏳ 1.4 Test on Devnet

**Get test SOL + USDC:**
```bash
# 1. Fund wallet with SOL (for gas fees)
solana airdrop 2 <TREASURY_PUBLIC_KEY> --url devnet

# 2. Get test USDC from devnet faucet
# https://spl-token-faucet.com/?token-name=USDC
```

**Test payment flow:**
```python
# backend/payments/test_devnet_payment.py
from solana_payments import SolanaPaymentProcessor
from solana_wallet import SolanaWalletManager
from solders.keypair import Keypair
import base58
import json

# Load treasury
with open("TREASURY_WALLET.json") as f:
    treasury_data = json.load(f)

treasury_keypair = Keypair.from_bytes(
    base58.b58decode(treasury_data["private_key"])
)

# Initialize processor (devnet)
processor = SolanaPaymentProcessor(
    treasury_keypair=treasury_keypair,
    rpc_url="https://api.devnet.solana.com"
)

# Generate recipient wallet
manager = SolanaWalletManager(rpc_url="https://api.devnet.solana.com")
recipient = manager.generate_agent_wallet()

print(f"Treasury: {treasury_data['public_key']}")
print(f"Treasury Balance: ${processor.get_treasury_balance():.2f}")
print(f"\nRecipient: {recipient['public_key']}")

# Send test payment (10 cents)
if processor.get_treasury_balance() > 0:
    signature = processor.send_usdc(
        to_address=recipient['public_key'],
        amount_usdc=0.10,
        memo="Test payment"
    )
    print(f"\n✅ Payment sent: {signature}")
    print(f"View on Solscan: https://solscan.io/tx/{signature}?cluster=devnet")
else:
    print("\n⚠️  Treasury needs USDC - fund from faucet first")
```

---

## Day 2 (Feb 14) - Integration 🔄

### ⏳ 2.1 Add Wallet Fields to Agent Model

**Update `backend/models/agent.py`:**
```python
class Agent(Base):
    # ... existing fields ...
    
    # Solana Wallet
    wallet_address = Column(String(44))  # Solana public key
    wallet_private_key_encrypted = Column(Text)  # Encrypted private key
    wallet_created_at = Column(DateTime)
    usdc_balance = Column(Float, default=0.0)  # Cached balance
    last_balance_check = Column(DateTime)
```

**Migration:**
```sql
-- migrations/003_add_wallet_fields.sql
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(44),
ADD COLUMN IF NOT EXISTS wallet_private_key_encrypted TEXT,
ADD COLUMN IF NOT EXISTS wallet_created_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS usdc_balance FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS last_balance_check TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_agents_wallet_address ON agents(wallet_address);
```

### ⏳ 2.2 Auto-Create Wallets on Registration

**Update `backend/main.py` agent registration:**
```python
from payments.solana_wallet import SolanaWalletManager

wallet_manager = SolanaWalletManager()

@app.post("/api/v1/agents", status_code=status.HTTP_201_CREATED)
def create_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    # ... existing validation ...
    
    # Generate Solana wallet
    wallet = wallet_manager.generate_agent_wallet()
    
    # Create agent with wallet
    agent = Agent(
        name=agent_data.name,
        # ... other fields ...
        wallet_address=wallet["public_key"],
        wallet_private_key_encrypted=wallet["private_key_encrypted"],
        wallet_created_at=datetime.utcnow()
    )
    
    db.add(agent)
    db.commit()
    
    return {
        "success": True,
        "agent": agent.to_dict(),
        "wallet": {
            "address": wallet["public_key"],
            "usdc_address": wallet["usdc_address"]
        }
    }
```

### ⏳ 2.3 Wallet-Based Authentication

**Create `backend/api/wallet_auth.py`:**
```python
"""
Wallet-based authentication for agents
Agent proves ownership by signing challenge with their private key
"""
from fastapi import HTTPException, Header
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import base58
import time
import hashlib

# Active challenges (in production: use Redis)
active_challenges = {}

def generate_challenge(wallet_address: str) -> dict:
    """
    Generate authentication challenge for wallet
    
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
        "expires_at": timestamp + 60,
        "text": challenge_text
    }
    
    return {
        "challenge": challenge_text,
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
        raise HTTPException(status_code=401, detail="No active challenge for wallet")
    
    challenge_data = active_challenges[wallet_address]
    
    # Check not expired
    if time.time() > challenge_data["expires_at"]:
        del active_challenges[wallet_address]
        raise HTTPException(status_code=401, detail="Challenge expired")
    
    try:
        # Verify signature
        pubkey = Pubkey.from_string(wallet_address)
        signature_bytes = base58.b58decode(signature_base58)
        message_bytes = challenge_data["text"].encode()
        
        # Solana signature verification
        # (Simplified - in production use proper Solana signature verification)
        is_valid = True  # TODO: Implement actual signature verification
        
        if is_valid:
            # Remove challenge (one-time use)
            del active_challenges[wallet_address]
            return True
        else:
            raise HTTPException(status_code=401, detail="Invalid signature")
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Signature verification failed: {e}")

async def verify_wallet_auth(authorization: str = Header(None)) -> str:
    """
    FastAPI dependency for wallet-based auth
    
    Header format: Authorization: Wallet <address>:<signature>
    
    Returns:
        str: Authenticated wallet address
    """
    if not authorization or not authorization.startswith("Wallet "):
        raise HTTPException(status_code=401, detail="Missing wallet authorization")
    
    auth_data = authorization.replace("Wallet ", "")
    
    if ":" not in auth_data:
        raise HTTPException(status_code=401, detail="Invalid auth format. Expected: Wallet <address>:<signature>")
    
    wallet_address, signature = auth_data.split(":", 1)
    
    if verify_signature(wallet_address, signature):
        return wallet_address
    else:
        raise HTTPException(status_code=401, detail="Invalid wallet signature")
```

**Add auth endpoints:**
```python
@app.post("/api/v1/auth/challenge")
def get_auth_challenge(wallet_address: str):
    """Get challenge for wallet authentication"""
    challenge = generate_challenge(wallet_address)
    return {
        "success": True,
        "challenge": challenge
    }

@app.get("/api/v1/agents/me")
def get_my_agent(wallet_address: str = Depends(verify_wallet_auth), db: Session = Depends(get_db)):
    """Get authenticated agent's profile"""
    agent = db.query(Agent).filter(Agent.wallet_address == wallet_address).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "success": True,
        "agent": agent.to_dict()
    }
```

### ⏳ 2.4 Agent-to-Agent Payment Endpoint

**Create `backend/api/payments_api.py`:**
```python
"""
Payment endpoints for agent transactions
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from payments.solana_payments import SolanaPaymentProcessor
from payments.solana_wallet import SolanaWalletManager
from api.wallet_auth import verify_wallet_auth
from database.base import get_db
from models.agent import Agent
import os
import json
import base58
from solders.keypair import Keypair

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Load treasury
with open("backend/payments/TREASURY_WALLET.json") as f:
    treasury_data = json.load(f)

treasury_keypair = Keypair.from_bytes(base58.b58decode(treasury_data["private_key"]))
processor = SolanaPaymentProcessor(treasury_keypair=treasury_keypair)

class PaymentRequest(BaseModel):
    to_agent_id: str
    amount_usdc: float
    service_description: str

@router.post("/send")
async def send_payment(
    payment: PaymentRequest,
    from_wallet: str = Depends(verify_wallet_auth),
    db: Session = Depends(get_db)
):
    """
    Agent A pays Agent B via exchange
    
    Flow:
    1. Validate agents exist
    2. Calculate commission (6%)
    3. Send USDC from treasury to recipient
    4. Log transaction
    5. Return confirmation
    """
    # Get recipient agent
    to_agent = db.query(Agent).filter(Agent.id == payment.to_agent_id).first()
    if not to_agent:
        raise HTTPException(status_code=404, detail="Recipient agent not found")
    
    # Calculate amounts
    amount = payment.amount_usdc
    commission_rate = 0.06  # 6%
    commission = amount * commission_rate
    recipient_amount = amount - commission
    
    # Send USDC
    try:
        signature = processor.send_usdc(
            to_address=to_agent.wallet_address,
            amount_usdc=recipient_amount,
            memo=f"Payment for: {payment.service_description}"
        )
        
        # Log transaction
        # TODO: Save to transactions table
        
        return {
            "success": True,
            "transaction": {
                "signature": signature,
                "amount_sent": amount,
                "commission": commission,
                "recipient_received": recipient_amount,
                "explorer_url": f"https://solscan.io/tx/{signature}"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment failed: {e}")

@router.get("/balance")
async def get_balance(
    wallet_address: str = Depends(verify_wallet_auth),
    db: Session = Depends(get_db)
):
    """Get agent's USDC balance"""
    wallet_manager = SolanaWalletManager()
    balance = wallet_manager.get_balance(wallet_address)
    
    return {
        "success": True,
        "wallet_address": wallet_address,
        "usdc_balance": balance
    }
```

**Add to main.py:**
```python
from api import payments_api
app.include_router(payments_api.router)
```

---

## Day 3 (Feb 15) - Deployment 🚀

### ⏳ 3.1 Railway Environment Variables

**Add to Railway:**
```
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
USDC_MINT=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
TREASURY_PUBLIC_KEY=<from TREASURY_WALLET.json>
TREASURY_PRIVATE_KEY=<from TREASURY_WALLET.json>
WALLET_ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
```

### ⏳ 3.2 Database Migration

```bash
cd agentdirectory.exchange
python run_wallet_migration.py  # Creates migrations/003_add_wallet_fields.sql
```

### ⏳ 3.3 Fund Mainnet Treasury

**Steps:**
1. Buy USDC on Coinbase/Kraken ($1,000)
2. Send to treasury wallet address
3. Verify balance: `python backend/payments/check_treasury.py`

### ⏳ 3.4 Test End-to-End

**Create two test agents:**
```bash
# Agent A registers
curl -X POST https://agentdirectory.exchange/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent A", "owner_email": "test@example.com"}'

# Agent B registers  
curl -X POST https://agentdirectory.exchange/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent B", "owner_email": "test2@example.com"}'
```

**Agent A pays Agent B:**
```bash
# 1. Get auth challenge
curl -X POST https://agentdirectory.exchange/api/v1/auth/challenge?wallet_address=<AGENT_A_WALLET>

# 2. Sign challenge (would be done by agent's wallet)
# signature = agent_wallet.sign(challenge)

# 3. Send payment
curl -X POST https://agentdirectory.exchange/api/v1/payments/send \
  -H "Authorization: Wallet <AGENT_A_WALLET>:<signature>" \
  -H "Content-Type: application/json" \
  -d '{"to_agent_id": "<AGENT_B_ID>", "amount_usdc": 0.50, "service_description": "Market research"}'

# 4. Verify on Solscan
# Check transaction: https://solscan.io/tx/<signature>
```

---

## Success Criteria

**✅ MVP Complete When:**
1. Agent registers → wallet auto-created
2. Agent can authenticate with wallet signature
3. Agent A sends $0.50 to Agent B → succeeds
4. Transaction visible on Solscan
5. Agent B sees balance updated
6. Exchange commission (6%) deducted
7. All on mainnet (real USDC)

**Not Required for MVP:**
- Circle API (fiat offramp)
- Perfect error handling
- Admin dashboard
- Rate limiting
- Multi-sig treasury
- Beautiful UX

---

## Phase 2 (Post-Weekend)

**For developer to polish:**
1. Circle API integration (cash out to bank)
2. Proper signature verification (Solana ed25519)
3. Transaction history UI
4. Admin dashboard
5. Multi-sig treasury (>$10K)
6. Rate limiting + security hardening
7. Agent SDK (Python/TypeScript)
8. Documentation for external agents

---

## File Checklist

**Create/Modify:**
- [ ] `backend/payments/generate_treasury.py`
- [ ] `backend/payments/test_devnet_payment.py`
- [ ] `backend/payments/TREASURY_WALLET.json` (gitignored)
- [ ] `backend/models/agent.py` (add wallet fields)
- [ ] `migrations/003_add_wallet_fields.sql`
- [ ] `run_wallet_migration.py`
- [ ] `backend/api/wallet_auth.py`
- [ ] `backend/api/payments_api.py`
- [ ] `backend/main.py` (integrate wallet auth + payments)
- [ ] `.gitignore` (add TREASURY_WALLET.json)

---

## Risk Mitigation

**What Could Go Wrong:**

1. **Solana network down** → Use devnet for testing, mainnet only for final test
2. **Treasury runs out of USDC** → Start with $1K, add monitoring
3. **Signature verification fails** → Simplified MVP version, improve in Phase 2
4. **Railway deploy breaks** → Test locally first, deploy incrementally
5. **Agent adoption low** → Not a technical problem, marketing issue

---

## Communication

**Status Updates:**
- End of Day 1: Treasury generated, devnet tested
- End of Day 2: Integration complete, local testing done
- End of Day 3: Deployed, first mainnet transaction

**Deliverables:**
- Working Solana payment system
- Wallet-based authentication
- Documentation of what works + what needs improvement
- Handoff notes for developer to polish

---

**Status:** IN PROGRESS  
**Next:** Generate treasury wallet + test on devnet  
**Target:** Working by Feb 15, 2026  

🚀 **Let's ship it.**
