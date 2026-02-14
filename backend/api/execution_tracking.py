"""
Execution Tracking API Endpoints
Records agent task executions for reputation calculation
Phase 1.4: Transaction Tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from ..db import get_db_connection

router = APIRouter(prefix="/api/v1/executions", tags=["executions"])


# Pydantic Models
class ExecutionStart(BaseModel):
    requesting_agent_id: str
    executing_agent_id: str
    capability_requested: str
    task_type: Optional[str] = None
    task_hash: Optional[str] = None
    quoted_cost_usd: float
    escrow_address: Optional[str] = None
    protocol_version: str = "1.0"


class ExecutionComplete(BaseModel):
    execution_id: str
    success: bool
    execution_time_ms: int
    actual_cost_usd: float
    payment_tx_hash: Optional[str] = None
    result_hash: Optional[str] = None
    result_size_bytes: Optional[int] = None
    quality_rating: Optional[int] = None  # 1-5 stars


class ExecutionFailed(BaseModel):
    execution_id: str
    error_code: str
    error_message: Optional[str] = None


@router.post("/start")
async def start_execution(request: ExecutionStart):
    """
    Record the start of an agent execution
    Called when agent accepts a task
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    execution_id = str(uuid.uuid4())
    
    try:
        cur.execute("""
            INSERT INTO agent_executions (
                id, requesting_agent_id, executing_agent_id,
                capability_requested, task_type, task_hash,
                quoted_cost_usd, escrow_address, protocol_version,
                status, started_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            execution_id,
            request.requesting_agent_id,
            request.executing_agent_id,
            request.capability_requested,
            request.task_type,
            request.task_hash,
            request.quoted_cost_usd,
            request.escrow_address,
            request.protocol_version,
            'processing',
            datetime.now()
        ))
        
        conn.commit()
        
        return {
            "execution_id": execution_id,
            "status": "processing",
            "message": "Execution started and being tracked"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record execution start: {e}")
    finally:
        cur.close()
        conn.close()


@router.post("/complete")
async def complete_execution(request: ExecutionComplete):
    """
    Record successful execution completion
    Triggers reputation recalculation
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Update execution record
        cur.execute("""
            UPDATE agent_executions
            SET status = 'completed',
                success = %s,
                completed_at = %s,
                execution_time_ms = %s,
                actual_cost_usd = %s,
                payment_tx_hash = %s,
                result_hash = %s,
                result_size_bytes = %s,
                quality_rating = %s,
                updated_at = %s
            WHERE id = %s
            RETURNING executing_agent_id, capability_requested
        """, (
            request.success,
            datetime.now(),
            request.execution_time_ms,
            request.actual_cost_usd,
            request.payment_tx_hash,
            request.result_hash,
            request.result_size_bytes,
            request.quality_rating,
            datetime.now(),
            request.execution_id
        ))
        
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        executing_agent_id, capability = result
        
        # Update proven capabilities
        if request.success:
            cur.execute("""
                INSERT INTO agent_proven_capabilities (
                    agent_id, capability, execution_count, success_rate,
                    avg_cost_usd, last_proven_at
                )
                VALUES (%s, %s, 1, 1.0, %s, %s)
                ON CONFLICT (agent_id, capability) DO UPDATE
                SET execution_count = agent_proven_capabilities.execution_count + 1,
                    last_proven_at = %s
            """, (
                executing_agent_id,
                capability,
                request.actual_cost_usd,
                datetime.now(),
                datetime.now()
            ))
        
        conn.commit()
        
        # Trigger reputation recalculation (async job)
        # For now, just flag that it needs updating
        
        return {
            "status": "recorded",
            "execution_id": request.execution_id,
            "message": "Execution completion recorded, reputation will be updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record completion: {e}")
    finally:
        cur.close()
        conn.close()


@router.post("/fail")
async def fail_execution(request: ExecutionFailed):
    """
    Record execution failure
    Affects agent reputation
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE agent_executions
            SET status = 'failed',
                success = false,
                completed_at = %s,
                error_code = %s,
                error_message = %s,
                updated_at = %s
            WHERE id = %s
            RETURNING executing_agent_id
        """, (
            datetime.now(),
            request.error_code,
            request.error_message,
            datetime.now(),
            request.execution_id
        ))
        
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        conn.commit()
        
        return {
            "status": "recorded",
            "execution_id": request.execution_id,
            "message": "Failure recorded, reputation will be updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record failure: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    """
    Get execution details
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                id, requesting_agent_id, executing_agent_id,
                capability_requested, status, started_at, completed_at,
                execution_time_ms, quoted_cost_usd, actual_cost_usd,
                success, quality_rating
            FROM agent_executions
            WHERE id = %s
        """, (execution_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "execution_id": str(row[0]),
            "requesting_agent": row[1],
            "executing_agent": str(row[2]),
            "capability": row[3],
            "status": row[4],
            "started_at": row[5].isoformat() if row[5] else None,
            "completed_at": row[6].isoformat() if row[6] else None,
            "execution_time_ms": row[7],
            "quoted_cost_usd": float(row[8]) if row[8] else None,
            "actual_cost_usd": float(row[9]) if row[9] else None,
            "success": row[10],
            "quality_rating": row[11]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch execution: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/agent/{agent_id}/history")
async def get_agent_execution_history(
    agent_id: str,
    limit: int = 100,
    status: Optional[str] = None
):
    """
    Get execution history for an agent
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT 
                id, requesting_agent_id, capability_requested,
                status, started_at, completed_at, execution_time_ms,
                actual_cost_usd, success, quality_rating
            FROM agent_executions
            WHERE executing_agent_id = %s
        """
        params = [agent_id]
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY started_at DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        executions = []
        for row in rows:
            executions.append({
                "execution_id": str(row[0]),
                "requesting_agent": row[1],
                "capability": row[2],
                "status": row[3],
                "started_at": row[4].isoformat() if row[4] else None,
                "completed_at": row[5].isoformat() if row[5] else None,
                "execution_time_ms": row[6],
                "actual_cost_usd": float(row[7]) if row[7] else None,
                "success": row[8],
                "quality_rating": row[9]
            })
        
        return {
            "agent_id": agent_id,
            "total": len(executions),
            "executions": executions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")
    finally:
        cur.close()
        conn.close()


@router.get("/stats/summary")
async def get_execution_stats():
    """
    Get overall execution statistics
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Total executions
        cur.execute("SELECT COUNT(*) FROM agent_executions")
        total = cur.fetchone()[0]
        
        # By status
        cur.execute("""
            SELECT status, COUNT(*) 
            FROM agent_executions 
            GROUP BY status
        """)
        by_status = {row[0]: row[1] for row in cur.fetchall()}
        
        # Success rate
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE success = true) as successful,
                COUNT(*) FILTER (WHERE success = false) as failed
            FROM agent_executions
            WHERE status IN ('completed', 'failed')
        """)
        success_data = cur.fetchone()
        success_rate = success_data[0] / (success_data[0] + success_data[1]) if (success_data[0] + success_data[1]) > 0 else 0
        
        # Average execution time
        cur.execute("""
            SELECT AVG(execution_time_ms)
            FROM agent_executions
            WHERE execution_time_ms IS NOT NULL
        """)
        avg_time = cur.fetchone()[0] or 0
        
        return {
            "total_executions": total,
            "by_status": by_status,
            "overall_success_rate": round(success_rate, 4),
            "avg_execution_time_ms": int(avg_time)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {e}")
    finally:
        cur.close()
        conn.close()
