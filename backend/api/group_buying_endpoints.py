"""
Group Buying Pool API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from database.base import get_db_connection

router = APIRouter(prefix="/api/v1/pools", tags=["group-buying"])

REFERRAL_SECTION = {
    "your_code": "REF-XXXX",
    "earnings_to_date": 0.0,
    "invite_url": "https://agentdirectory.exchange/ref/REF-XXXX",
    "message": "Earn 10% for 90 days + 0.5% forever"
}


# --- Pydantic Models ---

class PoolCreate(BaseModel):
    service_id: str
    creator_agent_id: str
    target_quantity: int
    discount_tier: str  # e.g. "10%", "20%", "30%"
    expires_in_hours: Optional[int] = 72


class PoolJoin(BaseModel):
    agent_id: str
    quantity: int = 1


class PoolResponse(BaseModel):
    id: str
    service_id: str
    creator_agent_id: str
    target_quantity: int
    current_quantity: int
    discount_tier: str
    participants: list
    status: str
    expires_at: Optional[datetime]
    created_at: Optional[datetime]


# --- Endpoints ---

@router.post("/")
async def create_pool(pool: PoolCreate):
    """Create a new group buying pool"""
    pool_id = str(uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=pool.expires_in_hours)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO group_buying_pools
               (id, service_id, creator_agent_id, target_quantity, current_quantity,
                discount_tier, participants, status, expires_at)
               VALUES (%s,%s,%s,%s,0,%s,%s,'active',%s)
               RETURNING id""",
            (pool_id, pool.service_id, pool.creator_agent_id, pool.target_quantity,
             pool.discount_tier, '[]', expires_at)
        )
        conn.commit()
        return {"id": pool_id, "status": "active", "expires_at": str(expires_at), "referral": REFERRAL_SECTION}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/")
async def list_pools(
    status: Optional[str] = "active",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List active group buying pools"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        conditions = []
        params = []
        if status:
            conditions.append("status = %s")
            params.append(status)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])
        cur.execute(
            f"""SELECT id, service_id, creator_agent_id, target_quantity, current_quantity,
                       discount_tier, participants, status, expires_at, created_at
                FROM group_buying_pools {where}
                ORDER BY created_at DESC LIMIT %s OFFSET %s""",
            params
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        pools = [dict(zip(cols, row)) for row in rows]
        return {"pools": pools, "total": len(pools), "referral": REFERRAL_SECTION}
    finally:
        conn.close()


@router.get("/{pool_id}")
async def get_pool(pool_id: str):
    """Get pool status and details"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, service_id, creator_agent_id, target_quantity, current_quantity,
                      discount_tier, participants, status, triggered_at, expires_at, created_at
               FROM group_buying_pools WHERE id = %s""",
            (pool_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pool not found")
        cols = [desc[0] for desc in cur.description]
        pool = dict(zip(cols, row))
        progress = (pool["current_quantity"] / pool["target_quantity"] * 100) if pool["target_quantity"] > 0 else 0
        pool["progress_pct"] = round(progress, 1)
        return {"pool": pool, "referral": REFERRAL_SECTION}
    finally:
        conn.close()


@router.post("/{pool_id}/join")
async def join_pool(pool_id: str, join: PoolJoin):
    """Join an existing group buying pool"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Get current pool
        cur.execute("SELECT status, current_quantity, target_quantity, participants FROM group_buying_pools WHERE id = %s FOR UPDATE", (pool_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pool not found")
        status, current_qty, target_qty, participants = row
        if status != "active":
            raise HTTPException(status_code=400, detail=f"Pool is {status}, cannot join")

        new_qty = current_qty + join.quantity
        import json
        parts = json.loads(participants) if isinstance(participants, str) else (participants or [])
        parts.append({"agent_id": join.agent_id, "quantity": join.quantity, "joined_at": datetime.utcnow().isoformat()})

        # Auto-trigger if threshold met
        new_status = "triggered" if new_qty >= target_qty else "active"
        triggered_at = "NOW()" if new_status == "triggered" else "NULL"

        cur.execute(
            f"""UPDATE group_buying_pools
                SET current_quantity = %s, participants = %s, status = %s,
                    triggered_at = {triggered_at}, updated_at = NOW()
                WHERE id = %s""",
            (new_qty, json.dumps(parts), new_status, pool_id)
        )
        conn.commit()
        return {
            "pool_id": pool_id,
            "current_quantity": new_qty,
            "target_quantity": target_qty,
            "status": new_status,
            "referral": REFERRAL_SECTION
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{pool_id}/trigger")
async def trigger_pool(pool_id: str):
    """Manually trigger a pool if threshold is met"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT current_quantity, target_quantity, status FROM group_buying_pools WHERE id = %s", (pool_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pool not found")
        current_qty, target_qty, status = row
        if status == "triggered":
            return {"pool_id": pool_id, "status": "already_triggered", "referral": REFERRAL_SECTION}
        if current_qty < target_qty:
            raise HTTPException(status_code=400, detail=f"Threshold not met: {current_qty}/{target_qty}")

        cur.execute(
            "UPDATE group_buying_pools SET status = 'triggered', triggered_at = NOW(), updated_at = NOW() WHERE id = %s",
            (pool_id,)
        )
        conn.commit()
        return {"pool_id": pool_id, "status": "triggered", "referral": REFERRAL_SECTION}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
