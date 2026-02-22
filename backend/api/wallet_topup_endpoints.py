"""
Wallet Auto Top-Up API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4

from database.base import get_db_connection

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])

REFERRAL_SECTION = {
    "your_code": "REF-XXXX",
    "earnings_to_date": 0.0,
    "invite_url": "https://agentdirectory.exchange/ref/REF-XXXX",
    "message": "Earn 10% for 90 days + 0.5% forever"
}


# --- Pydantic Models ---

class AutoTopUpConfigure(BaseModel):
    agent_id: str
    floor_balance_usd: float
    refill_amount_usd: float
    payment_method: str  # e.g. "stripe", "crypto_usdc", "crypto_sol"
    payment_token: Optional[str] = None  # tokenized payment method ID


class AutoTopUpStatus(BaseModel):
    agent_id: str
    floor_balance_usd: float
    refill_amount_usd: float
    payment_method: str
    is_active: bool
    last_topup_at: Optional[str]
    total_topups: int


class AutoTopUpDisable(BaseModel):
    agent_id: str


# --- Endpoints ---

@router.post("/auto-topup/configure")
async def configure_auto_topup(config: AutoTopUpConfigure):
    """Configure auto top-up: set floor balance, refill amount, and payment method"""
    config_id = str(uuid4())
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Upsert: update if agent already has config, else insert
        cur.execute(
            """INSERT INTO wallet_auto_topup
               (id, agent_id, floor_balance_usd, refill_amount_usd, payment_method, payment_token, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, true)
               ON CONFLICT (agent_id) DO UPDATE SET
                   floor_balance_usd = EXCLUDED.floor_balance_usd,
                   refill_amount_usd = EXCLUDED.refill_amount_usd,
                   payment_method = EXCLUDED.payment_method,
                   payment_token = EXCLUDED.payment_token,
                   is_active = true,
                   updated_at = NOW()
               RETURNING id""",
            (config_id, config.agent_id, config.floor_balance_usd,
             config.refill_amount_usd, config.payment_method, config.payment_token)
        )
        conn.commit()
        return {
            "status": "configured",
            "agent_id": config.agent_id,
            "floor_balance_usd": config.floor_balance_usd,
            "refill_amount_usd": config.refill_amount_usd,
            "payment_method": config.payment_method,
            "referral": REFERRAL_SECTION
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/auto-topup/status")
async def get_auto_topup_status(agent_id: str):
    """Check auto top-up configuration status"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT agent_id, floor_balance_usd, refill_amount_usd, payment_method,
                      is_active, last_topup_at, total_topups
               FROM wallet_auto_topup WHERE agent_id = %s""",
            (agent_id,)
        )
        row = cur.fetchone()
        if not row:
            return {"configured": False, "agent_id": agent_id, "referral": REFERRAL_SECTION}
        cols = [desc[0] for desc in cur.description]
        config = dict(zip(cols, row))
        config["configured"] = True
        config["referral"] = REFERRAL_SECTION
        return config
    finally:
        conn.close()


@router.delete("/auto-topup")
async def disable_auto_topup(req: AutoTopUpDisable):
    """Disable auto top-up for an agent"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE wallet_auto_topup SET is_active = false, updated_at = NOW() WHERE agent_id = %s RETURNING id",
            (req.agent_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No auto top-up config found for this agent")
        conn.commit()
        return {"status": "disabled", "agent_id": req.agent_id, "referral": REFERRAL_SECTION}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
