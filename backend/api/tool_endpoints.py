"""
Tool Registry API Endpoints (MCP Tools Marketplace)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
from uuid import uuid4
import httpx

from database.base import get_db, get_db_connection
from api.agent_auth import get_current_agent
from api.rate_limiting import check_rate_limit, consume_call_credit
from models.agent import Agent
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])

REFERRAL_SECTION = {
    "your_code": "REF-XXXX",
    "earnings_to_date": 0.0,
    "invite_url": "https://agentdirectory.exchange/ref/REF-XXXX",
    "message": "Earn 10% for 90 days + 0.5% forever"
}


# --- Pydantic Models ---

class ToolCreate(BaseModel):
    name: str
    description: Optional[str] = None
    author_agent_id: str
    package_name: str
    install_command: Optional[str] = None
    modules: Optional[list] = None
    pricing_model: str = "free"
    price_usd: Optional[float] = 0.0
    monthly_price_usd: Optional[float] = 0.0
    per_call_price_usd: Optional[float] = 0.0
    category: Optional[str] = None
    tags: Optional[list] = None
    protocol: str = "mcp"
    version: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    install_command: Optional[str] = None
    modules: Optional[list] = None
    pricing_model: Optional[str] = None
    price_usd: Optional[float] = None
    monthly_price_usd: Optional[float] = None
    per_call_price_usd: Optional[float] = None
    category: Optional[str] = None
    tags: Optional[list] = None
    protocol: Optional[str] = None
    version: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None


class ToolResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    author_agent_id: str
    package_name: str
    install_command: Optional[str]
    modules: Optional[list]
    pricing_model: str
    price_usd: Optional[float]
    monthly_price_usd: Optional[float]
    per_call_price_usd: Optional[float]
    category: Optional[str]
    tags: Optional[list]
    protocol: str
    version: Optional[str]
    repository_url: Optional[str]
    documentation_url: Optional[str]
    total_installs: int
    total_calls: int
    avg_rating: float
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# --- Endpoints ---

@router.get("/featured")
async def get_featured_tools(limit: int = Query(10, ge=1, le=50)):
    """Get featured/popular tools sorted by installs and rating"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, name, description, author_agent_id, package_name, install_command,
                      modules, pricing_model, price_usd, monthly_price_usd, per_call_price_usd,
                      category, tags, protocol, version, repository_url, documentation_url,
                      total_installs, total_calls, avg_rating, is_active, is_verified,
                      created_at, updated_at
               FROM tools WHERE is_active = true
               ORDER BY total_installs DESC, avg_rating DESC
               LIMIT %s""",
            (limit,)
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        tools = [dict(zip(cols, row)) for row in rows]
        return {"tools": tools, "total": len(tools), "referral": REFERRAL_SECTION}
    finally:
        conn.close()


@router.post("/")
async def register_tool(tool: ToolCreate):
    """Register a new MCP tool listing"""
    tool_id = str(uuid4())
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO tools (id, name, description, author_agent_id, package_name,
                      install_command, modules, pricing_model, price_usd, monthly_price_usd,
                      per_call_price_usd, category, tags, protocol, version,
                      repository_url, documentation_url)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING id""",
            (tool_id, tool.name, tool.description, tool.author_agent_id, tool.package_name,
             tool.install_command, str(tool.modules) if tool.modules else None,
             tool.pricing_model, tool.price_usd, tool.monthly_price_usd,
             tool.per_call_price_usd, tool.category,
             str(tool.tags) if tool.tags else None,
             tool.protocol, tool.version, tool.repository_url, tool.documentation_url)
        )
        conn.commit()
        return {"id": tool_id, "status": "registered", "referral": REFERRAL_SECTION}
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Package name already exists")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/")
async def list_tools(
    protocol: Optional[str] = None,
    category: Optional[str] = None,
    pricing_model: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List/search tools with filters"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        conditions = ["is_active = true"]
        params = []

        if protocol:
            conditions.append("protocol = %s")
            params.append(protocol)
        if category:
            conditions.append("category = %s")
            params.append(category)
        if pricing_model:
            conditions.append("pricing_model = %s")
            params.append(pricing_model)
        if tags:
            conditions.append("tags::text ILIKE %s")
            params.append(f"%{tags}%")
        if search:
            conditions.append("(name ILIKE %s OR description ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        where = " AND ".join(conditions)
        params.extend([limit, offset])

        cur.execute(
            f"""SELECT id, name, description, author_agent_id, package_name, install_command,
                       modules, pricing_model, price_usd, monthly_price_usd, per_call_price_usd,
                       category, tags, protocol, version, repository_url, documentation_url,
                       total_installs, total_calls, avg_rating, is_active, is_verified,
                       created_at, updated_at
                FROM tools WHERE {where}
                ORDER BY created_at DESC LIMIT %s OFFSET %s""",
            params
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        tools = [dict(zip(cols, row)) for row in rows]
        return {"tools": tools, "total": len(tools), "limit": limit, "offset": offset, "referral": REFERRAL_SECTION}
    finally:
        conn.close()


@router.get("/{tool_id}")
async def get_tool(tool_id: str):
    """Get tool details by ID"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, name, description, author_agent_id, package_name, install_command,
                      modules, pricing_model, price_usd, monthly_price_usd, per_call_price_usd,
                      category, tags, protocol, version, repository_url, documentation_url,
                      total_installs, total_calls, avg_rating, is_active, is_verified,
                      created_at, updated_at
               FROM tools WHERE id = %s""",
            (tool_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tool not found")
        cols = [desc[0] for desc in cur.description]
        return {"tool": dict(zip(cols, row)), "referral": REFERRAL_SECTION}
    finally:
        conn.close()


@router.put("/{tool_id}")
async def update_tool(tool_id: str, tool: ToolUpdate):
    """Update tool listing"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        updates = []
        params = []
        for field, value in tool.dict(exclude_unset=True).items():
            if value is not None:
                if field in ("modules", "tags"):
                    updates.append(f"{field} = %s")
                    params.append(str(value))
                else:
                    updates.append(f"{field} = %s")
                    params.append(value)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(tool_id)

        cur.execute(
            f"UPDATE tools SET {', '.join(updates)} WHERE id = %s RETURNING id",
            params
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Tool not found")
        conn.commit()
        return {"id": tool_id, "status": "updated", "referral": REFERRAL_SECTION}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{tool_id}/install")
async def record_install(tool_id: str):
    """Record a tool installation (increment counter)"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tools SET total_installs = total_installs + 1, updated_at = NOW() WHERE id = %s RETURNING total_installs",
            (tool_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tool not found")
        conn.commit()
        return {"tool_id": tool_id, "total_installs": row[0], "status": "installed", "referral": REFERRAL_SECTION}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{tool_id}/call")
async def record_call(tool_id: str):
    """Record a tool API call (usage metering)"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tools SET total_calls = total_calls + 1, updated_at = NOW() WHERE id = %s RETURNING total_calls, per_call_price_usd",
            (tool_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tool not found")
        conn.commit()
        return {
            "tool_id": tool_id,
            "total_calls": row[0],
            "call_cost_usd": row[1] or 0.0,
            "status": "recorded",
            "referral": REFERRAL_SECTION
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# --- Tool Execution Proxy (Agent-Ready) ---

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool"""
    parameters: Optional[dict[str, Any]] = None
    timeout_seconds: int = 30


class ToolExecutionResponse(BaseModel):
    """Response from tool execution"""
    success: bool
    tool_id: str
    tool_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    cost_usd: float
    credits_remaining: dict


@router.post("/{tool_id}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_id: str,
    request: ToolExecutionRequest,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Execute a tool through the platform (agent-ready endpoint)
    
    **Rate Limits:**
    - Free tier: 50 total calls, 5 calls/hour refill
    - Paid tier: No hourly limit, uses paid credits
    
    **Returns:**
    - Tool execution result
    - Credits consumed
    - Credits remaining
    
    **HTTP Status Codes:**
    - 200: Success
    - 401: Authentication failed
    - 404: Tool not found
    - 429: Rate limit exceeded
    - 500: Execution error
    """
    import time
    start_time = time.time()
    
    # Check rate limits
    limit_check = check_rate_limit(agent, db)
    
    if not limit_check["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=limit_check["reason"],
            headers={
                "X-RateLimit-Remaining": str(limit_check["limits"]["free_calls_remaining"]),
                "X-RateLimit-Reset": str(limit_check["limits"]["hourly_resets_in_seconds"]),
                "Retry-After": str(limit_check["limits"]["hourly_resets_in_seconds"])
            }
        )
    
    # Get tool details
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, name, per_call_price_usd, api_endpoint, is_active 
               FROM tools WHERE id = %s""",
            (tool_id,)
        )
        tool = cur.fetchone()
        
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        tool_id, tool_name, per_call_price, api_endpoint, is_active = tool
        
        if not is_active:
            raise HTTPException(status_code=400, detail="Tool is not active")
        
        if not api_endpoint:
            raise HTTPException(
                status_code=501,
                detail="Tool does not have an API endpoint configured"
            )
        
        # Consume call credit
        cost_usd = per_call_price or 0.005  # Default to $0.005 if not set
        consume_call_credit(agent, cost_usd, db)
        
        # Execute tool via HTTP proxy
        try:
            async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
                response = await client.post(
                    api_endpoint,
                    json=request.parameters or {},
                    headers={
                        "X-Agent-ID": str(agent.id),
                        "X-Tool-ID": tool_id,
                        "Content-Type": "application/json"
                    }
                )
                
                execution_time = int((time.time() - start_time) * 1000)
                
                # Record call metrics
                cur.execute(
                    "UPDATE tools SET total_calls = total_calls + 1, updated_at = NOW() WHERE id = %s",
                    (tool_id,)
                )
                conn.commit()
                
                # Get updated credits
                from api.rate_limiting import get_rate_limit_info
                credits_info = get_rate_limit_info(agent)
                
                if response.status_code >= 400:
                    return ToolExecutionResponse(
                        success=False,
                        tool_id=tool_id,
                        tool_name=tool_name,
                        error=f"Tool returned HTTP {response.status_code}: {response.text}",
                        execution_time_ms=execution_time,
                        cost_usd=cost_usd,
                        credits_remaining=credits_info
                    )
                
                return ToolExecutionResponse(
                    success=True,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    result=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    execution_time_ms=execution_time,
                    cost_usd=cost_usd,
                    credits_remaining=credits_info
                )
                
        except httpx.TimeoutException:
            # Refund credit on timeout
            if agent.paid_calls_remaining and agent.paid_calls_remaining > 0:
                agent.paid_calls_remaining += 1
            else:
                agent.free_calls_remaining += 1
                agent.hourly_calls_count -= 1
            db.commit()
            
            raise HTTPException(
                status_code=504,
                detail=f"Tool execution timed out after {request.timeout_seconds} seconds"
            )
        
        except Exception as e:
            # Refund credit on error
            if agent.paid_calls_remaining and agent.paid_calls_remaining > 0:
                agent.paid_calls_remaining += 1
            else:
                agent.free_calls_remaining += 1
                agent.hourly_calls_count -= 1
            db.commit()
            
            raise HTTPException(
                status_code=500,
                detail=f"Tool execution error: {str(e)}"
            )
    
    finally:
        conn.close()
