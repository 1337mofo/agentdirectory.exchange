"""
Instrument API Endpoints (Layer 1 - Agent Workflows)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

from database.base import get_db, get_db_connection

router = APIRouter(prefix="/api/v1/instruments", tags=["instruments"])


# Pydantic models
class InstrumentBase(BaseModel):
    name: str
    description: Optional[str]
    category: Optional[str]
    price_usd: float
    agent_count: Optional[int]


class InstrumentDetail(InstrumentBase):
    id: str
    agent_ids: List[str]
    workflow: Optional[dict]
    pricing_model: str
    bundle_discount_usd: float
    is_active: bool
    created_at: datetime


class InstrumentListResponse(BaseModel):
    instruments: List[InstrumentBase]
    total: int


class InstrumentExecutionRequest(BaseModel):
    wallet_address: str
    payment_tx_hash: str
    inputs: Optional[dict]


class InstrumentExecutionResponse(BaseModel):
    execution_id: str
    status: str
    message: str


@router.get("", response_model=InstrumentListResponse)
async def list_instruments(
    category: Optional[str] = None,
    active_only: bool = True
):
    """
    List all available instruments (agent workflows)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT 
            i.id, i.name, i.description, i.category, 
            i.price_usd, i.agent_ids
        FROM instruments i
        WHERE 1=1
    """
    params = []
    
    if active_only:
        query += " AND i.is_active = true"
    
    if category:
        query += " AND i.category = %s"
        params.append(category)
    
    query += " ORDER BY i.price_usd ASC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    
    instruments = []
    for row in rows:
        agent_ids = json.loads(row[5]) if row[5] else []
        instruments.append({
            "id": str(row[0]),
            "name": row[1],
            "description": row[2],
            "category": row[3],
            "price_usd": float(row[4]),
            "agent_count": len(agent_ids)
        })
    
    cur.close()
    conn.close()
    
    return {
        "instruments": instruments,
        "total": len(instruments)
    }


@router.get("/{instrument_id}", response_model=InstrumentDetail)
async def get_instrument(instrument_id: str):
    """
    Get detailed information about a specific instrument
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            id, name, description, agent_ids, workflow, category,
            pricing_model, price_usd, bundle_discount_usd,
            is_active, created_at
        FROM instruments
        WHERE id = %s
    """, (instrument_id,))
    
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    agent_ids = json.loads(row[3]) if row[3] else []
    workflow = json.loads(row[4]) if row[4] else None
    
    instrument = {
        "id": str(row[0]),
        "name": row[1],
        "description": row[2],
        "agent_ids": agent_ids,
        "workflow": workflow,
        "category": row[5],
        "pricing_model": row[6],
        "price_usd": float(row[7]),
        "bundle_discount_usd": float(row[8]) if row[8] else 0,
        "is_active": row[9],
        "created_at": row[10],
        "agent_count": len(agent_ids)
    }
    
    cur.close()
    conn.close()
    
    return instrument


@router.post("/{instrument_id}/execute", response_model=InstrumentExecutionResponse)
async def execute_instrument(
    instrument_id: str,
    request: InstrumentExecutionRequest
):
    """
    Execute an instrument workflow
    Payment must be verified before execution
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify instrument exists
    cur.execute("""
        SELECT id, name, price_usd, agent_ids, workflow
        FROM instruments
        WHERE id = %s AND is_active = true
    """, (instrument_id,))
    
    instrument = cur.fetchone()
    
    if not instrument:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Instrument not found or inactive")
    
    # TODO: Verify payment transaction on Solana
    # For now, accept payment_tx_hash as proof
    
    # Create execution record
    cur.execute("""
        INSERT INTO instrument_executions (
            instrument_id, user_wallet_address, 
            total_price_usd, payment_tx_hash, status
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        instrument_id,
        request.wallet_address,
        float(instrument[2]),
        request.payment_tx_hash,
        'pending'
    ))
    
    execution_id = cur.fetchone()[0]
    conn.commit()
    
    # TODO: Trigger workflow execution
    # For MVP, return execution_id for manual processing
    
    cur.close()
    conn.close()
    
    return {
        "execution_id": str(execution_id),
        "status": "pending",
        "message": f"Workflow execution started. Check status with execution_id: {execution_id}"
    }


@router.get("/{instrument_id}/executions/{execution_id}")
async def get_execution_status(instrument_id: str, execution_id: str):
    """
    Get status of a workflow execution
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            id, instrument_id, status, results, 
            created_at, completed_at
        FROM instrument_executions
        WHERE id = %s AND instrument_id = %s
    """, (execution_id, instrument_id))
    
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Execution not found")
    
    results = json.loads(row[3]) if row[3] else None
    
    execution = {
        "execution_id": str(row[0]),
        "instrument_id": str(row[1]),
        "status": row[2],
        "results": results,
        "created_at": row[4],
        "completed_at": row[5]
    }
    
    cur.close()
    conn.close()
    
    return execution
