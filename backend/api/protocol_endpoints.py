"""
Agent Transaction Protocol (ATP) v1.0 - API Endpoints
Standard protocol for agent-to-agent communication and trade
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import hashlib
import uuid

from database.base import get_db, get_db_connection

router = APIRouter(prefix="/api/v1/protocol", tags=["protocol"])


# Pydantic Models
class DiscoverRequest(BaseModel):
    requesting_agent_id: str
    capabilities_needed: List[str]
    constraints: Dict[str, Any]
    task_context: Optional[Dict[str, Any]] = None


class AgentMatch(BaseModel):
    agent_id: str
    name: str
    capabilities: List[str]
    reputation_score: float
    success_rate: float
    avg_latency_ms: int
    cost_usd: float
    execution_endpoint: str
    payment_addresses: Dict[str, str]
    verification_proof: str
    last_updated: datetime


class DiscoverResponse(BaseModel):
    matches: List[AgentMatch]
    match_quality: float
    estimated_total_cost: float
    platform_fee: float


class ReputationData(BaseModel):
    score: float
    total_executions: int
    successful_executions: int
    success_rate: float
    avg_response_time_ms: int
    cost_accuracy: float
    last_30_days: Dict[str, Any]


class VerifyResponse(BaseModel):
    agent_id: str
    verified: bool
    reputation: ReputationData
    network_data: Dict[str, Any]
    proof_of_work: Dict[str, Any]


class ExecutionTask(BaseModel):
    type: str
    input: Dict[str, Any]
    requirements: Dict[str, Any]


class ExecutionRequest(BaseModel):
    protocol_version: str
    requesting_agent: Dict[str, Any]
    task: ExecutionTask
    payment: Dict[str, Any]


class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    estimated_completion_ms: int
    cost_final_usd: float
    callback_registered: bool


class SettlementRequest(BaseModel):
    execution_id: str
    escrow_tx_hash: str
    status: str
    verification: Dict[str, Any]


class SettlementResponse(BaseModel):
    settlement_status: str
    payment_tx_hash: str
    amounts: Dict[str, float]
    reputation_updated: bool
    on_chain_record: str


# Helper Functions
def calculate_reputation_score(agent_data: dict) -> dict:
    """Calculate reputation score from transaction history"""
    total = agent_data.get('total_executions', 0)
    if total < 10:
        # Not enough data for reliable score
        return {
            "score": 0.5,
            "total_executions": total,
            "successful_executions": 0,
            "success_rate": 0,
            "avg_response_time_ms": 0,
            "cost_accuracy": 0,
            "last_30_days": {}
        }
    
    success = agent_data.get('successful_executions', 0)
    success_rate = success / total if total > 0 else 0
    
    # Weighted score calculation
    response_time_score = min(1.0, 5000 / agent_data.get('avg_response_time_ms', 5000))
    cost_accuracy = agent_data.get('cost_accuracy', 0.9)
    repeat_rate = agent_data.get('repeat_customer_rate', 0.5)
    peer_rating = agent_data.get('peer_rating', 4.0) / 5.0
    
    reputation_score = (
        0.40 * success_rate +
        0.20 * response_time_score +
        0.15 * cost_accuracy +
        0.15 * repeat_rate +
        0.10 * peer_rating
    )
    
    return {
        "score": round(reputation_score, 3),
        "total_executions": total,
        "successful_executions": success,
        "success_rate": round(success_rate, 3),
        "avg_response_time_ms": agent_data.get('avg_response_time_ms', 0),
        "cost_accuracy": round(cost_accuracy, 3),
        "last_30_days": agent_data.get('last_30_days', {})
    }


def match_agents_to_capabilities(capabilities: List[str], constraints: Dict, conn) -> List[Dict]:
    """Find agents matching capabilities and constraints"""
    cur = conn.cursor()
    
    # Build query based on capabilities (cast json to jsonb for containment operator)
    capability_conditions = " OR ".join([f"capabilities::jsonb @> '\[\"{cap}\"\]'" for cap in capabilities])
    
    query = f"""
        SELECT 
            id, name, description, capabilities, 
            pricing_model, api_endpoint, quality_score
        FROM agents
        WHERE ({capability_conditions})
        AND is_active = true
        AND quality_score >= %s
        ORDER BY quality_score DESC
        LIMIT 10
    """
    
    min_reputation = constraints.get('min_reputation', 0.5)
    min_quality = int(min_reputation * 100)
    
    cur.execute(query, (min_quality,))
    rows = cur.fetchall()
    
    matches = []
    for row in rows:
        agent_id = str(row[0])
        capabilities_json = json.loads(row[3]) if row[3] else []
        pricing_json = json.loads(row[4]) if row[4] else {}
        
        # Calculate reputation (mock for now)
        reputation = calculate_reputation_score({
            'total_executions': 100,
            'successful_executions': 95,
            'avg_response_time_ms': 3200,
            'cost_accuracy': 0.98,
            'repeat_customer_rate': 0.67,
            'peer_rating': 4.8
        })
        
        cost_usd = pricing_json.get('price_usd', 0)
        
        # Check cost constraint
        max_cost = constraints.get('max_cost_usd', float('inf'))
        if cost_usd > max_cost:
            continue
        
        matches.append({
            "agent_id": agent_id,
            "name": row[1],
            "capabilities": capabilities_json,
            "reputation_score": reputation['score'],
            "success_rate": reputation['success_rate'],
            "avg_latency_ms": reputation['avg_response_time_ms'],
            "cost_usd": float(cost_usd),
            "execution_endpoint": row[5] or f"https://agentdirectory.exchange/api/v1/execute/{agent_id}",
            "payment_addresses": {
                "solana_usdc": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"  # Mock
            },
            "verification_proof": hashlib.sha256(agent_id.encode()).hexdigest(),
            "last_updated": datetime.now().isoformat()
        })
    
    cur.close()
    return matches


# Protocol Endpoints

@router.post("/discover", response_model=DiscoverResponse)
async def discover_agents(request: DiscoverRequest):
    """
    Layer 1: Discovery
    Find agents matching required capabilities and constraints
    """
    conn = get_db_connection()
    
    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable. Protocol endpoints require database access."
        )
    
    try:
        matches = match_agents_to_capabilities(
            request.capabilities_needed,
            request.constraints,
            conn
        )
    finally:
        conn.close()
    
    if not matches:
        raise HTTPException(status_code=404, detail="No matching agents found")
    
    # Calculate match quality
    avg_reputation = sum(m['reputation_score'] for m in matches) / len(matches)
    match_quality = round(avg_reputation, 2)
    
    # Calculate costs
    estimated_cost = sum(m['cost_usd'] for m in matches[:1])  # Assume using first match
    platform_fee = round(estimated_cost * 0.02, 2)
    
    return {
        "matches": matches,
        "match_quality": match_quality,
        "estimated_total_cost": estimated_cost,
        "platform_fee": platform_fee
    }


@router.get("/verify/{agent_id}", response_model=VerifyResponse)
async def verify_agent(agent_id: str):
    """
    Layer 2: Verification
    Verify agent identity and retrieve reputation data
    """
    conn = get_db_connection()
    
    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable. Protocol endpoints require database access."
        )
    
    cur = conn.cursor()
    
    # Get agent data
    cur.execute("""
        SELECT id, name, quality_score
        FROM agents
        WHERE id = %s AND is_active = true
    """, (agent_id,))
    
    agent = cur.fetchone()
    
    if not agent:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Calculate reputation (mock data for now)
    reputation = calculate_reputation_score({
        'total_executions': 1247,
        'successful_executions': 1210,
        'avg_response_time_ms': 3200,
        'cost_accuracy': 0.98,
        'repeat_customer_rate': 0.67,
        'peer_rating': 4.8,
        'last_30_days': {
            'executions': 89,
            'success_rate': 0.96
        }
    })
    
    network_data = {
        "unique_requesters": 342,
        "repeat_customer_rate": 0.67,
        "peer_rating": 4.8
    }
    
    proof_of_work = {
        "recent_transactions": ["tx_hash_1", "tx_hash_2"],
        "on_chain_verification": "solana_signature_placeholder"
    }
    
    cur.close()
    conn.close()
    
    return {
        "agent_id": agent_id,
        "verified": True,
        "reputation": reputation,
        "network_data": network_data,
        "proof_of_work": proof_of_work
    }


@router.post("/execute", response_model=ExecutionResponse)
async def execute_agent(request: ExecutionRequest):
    """
    Layer 3: Execution
    Execute agent task with standard interface
    Note: This is a mock - actual execution happens at agent's endpoint
    """
    execution_id = str(uuid.uuid4())
    
    # In production, this would:
    # 1. Validate payment escrow
    # 2. Forward request to agent's execution_endpoint
    # 3. Register callback
    # 4. Track execution
    
    return {
        "execution_id": execution_id,
        "status": "processing",
        "estimated_completion_ms": 25000,
        "cost_final_usd": request.payment.get('amount_usd', 0),
        "callback_registered": True
    }


@router.post("/settle", response_model=SettlementResponse)
async def settle_transaction(request: SettlementRequest):
    """
    Layer 4: Settlement
    Settle payment after successful execution
    """
    # In production, this would:
    # 1. Verify execution completion
    # 2. Release escrow to executing agent
    # 3. Deduct platform fee
    # 4. Update reputations
    # 5. Record on-chain
    
    total_amount = 49.00  # Mock
    platform_fee = round(total_amount * 0.02, 2)
    to_agent = total_amount - platform_fee
    
    return {
        "settlement_status": "completed",
        "payment_tx_hash": "solana_tx_hash_placeholder",
        "amounts": {
            "total": total_amount,
            "to_agent": to_agent,
            "platform_fee": platform_fee
        },
        "reputation_updated": True,
        "on_chain_record": "solana_signature_placeholder"
    }


@router.get("/status")
async def protocol_status():
    """
    Get protocol status and statistics
    """
    return {
        "protocol_version": "1.0",
        "status": "operational",
        "endpoints": {
            "discover": "/api/v1/protocol/discover",
            "verify": "/api/v1/protocol/verify/{agent_id}",
            "execute": "/api/v1/protocol/execute",
            "settle": "/api/v1/protocol/settle"
        },
        "features": {
            "discovery": True,
            "reputation": True,
            "escrow": False,  # Coming soon
            "smart_contracts": False  # Coming soon
        },
        "statistics": {
            "total_agents": 291,
            "active_executions": 0,
            "total_transactions": 0,
            "avg_settlement_time_ms": 0
        }
    }
