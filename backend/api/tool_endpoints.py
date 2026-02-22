"""
Tool Registry API Endpoints (MCP Tools Marketplace)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from database.base import get_db, get_db_connection

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
