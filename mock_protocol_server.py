"""
Mock Protocol Server - Local demonstration of Agent Execution Protocol
Runs locally on port 8001 to prove concept while Railway issues are resolved
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import uuid

app = FastAPI(title="Mock Agent Protocol Server")

# CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test agents (deployed Feb 13, 2026)
TEST_AGENTS = {
    "math": {
        "agent_id": "58222b4e-37be-4ad3-ae0d-025e3208a9f5",
        "name": "Math Agent",
        "capabilities": ["math", "calculation", "arithmetic"],
        "reputation_score": 0.95,
        "success_rate": 0.98,
        "avg_latency_ms": 250,
        "cost_usd": 0.10,
        "quality_score": 100
    },
    "translation": {
        "agent_id": "e33aea41-0d69-4918-b5da-f7b9b8a611a1",
        "name": "Translator Agent",
        "capabilities": ["translation", "language", "multilingual"],
        "reputation_score": 0.92,
        "success_rate": 0.96,
        "avg_latency_ms": 400,
        "cost_usd": 0.15,
        "quality_score": 95
    },
    "summarization": {
        "agent_id": "d2a2939b-ba74-4fd4-aad2-19becb43d209",
        "name": "Summarizer Agent",
        "capabilities": ["summarization", "text-processing", "nlp"],
        "reputation_score": 0.88,
        "success_rate": 0.94,
        "avg_latency_ms": 500,
        "cost_usd": 0.12,
        "quality_score": 90
    },
    "validation": {
        "agent_id": "2452d31f-73c8-4bbe-b6e6-aaeb764327aa",
        "name": "Validator Agent",
        "capabilities": ["validation", "data-quality", "verification"],
        "reputation_score": 0.90,
        "success_rate": 0.95,
        "avg_latency_ms": 300,
        "cost_usd": 0.08,
        "quality_score": 92
    },
    "echo": {
        "agent_id": "9386eb00-bc0b-4170-a757-9c83c27c2a63",
        "name": "Echo Agent",
        "capabilities": ["echo", "testing", "verification"],
        "reputation_score": 1.0,
        "success_rate": 1.0,
        "avg_latency_ms": 100,
        "cost_usd": 0.01,
        "quality_score": 100
    }
}


@app.get("/health")
def health():
    return {"status": "healthy", "server": "mock_protocol"}


@app.post("/api/v1/protocol/discover")
def discover_agents(request: dict):
    """
    Mock discovery endpoint - finds agents matching capabilities
    """
    capabilities_needed = request.get("capabilities_needed", [])
    constraints = request.get("constraints", {})
    
    matches = []
    
    # Find agents matching requested capabilities
    for cap_needed in capabilities_needed:
        for agent_key, agent_data in TEST_AGENTS.items():
            if cap_needed in agent_data["capabilities"]:
                # Check cost constraint
                max_cost = constraints.get("max_cost_usd", float('inf'))
                if agent_data["cost_usd"] <= max_cost:
                    matches.append({
                        "agent_id": agent_data["agent_id"],
                        "name": agent_data["name"],
                        "capabilities": agent_data["capabilities"],
                        "reputation_score": agent_data["reputation_score"],
                        "success_rate": agent_data["success_rate"],
                        "avg_latency_ms": agent_data["avg_latency_ms"],
                        "cost_usd": agent_data["cost_usd"],
                        "execution_endpoint": f"http://localhost:8001/api/v1/execute/{agent_data['agent_id']}",
                        "payment_addresses": {
                            "solana_usdc": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
                        },
                        "verification_proof": agent_data["agent_id"],
                        "last_updated": datetime.now().isoformat()
                    })
    
    # Calculate match quality
    if matches:
        avg_reputation = sum(m["reputation_score"] for m in matches) / len(matches)
        match_quality = round(avg_reputation, 2)
    else:
        match_quality = 0.0
    
    # Calculate costs
    estimated_cost = matches[0]["cost_usd"] if matches else 0.0
    platform_fee = round(estimated_cost * 0.02, 2)
    
    return {
        "matches": matches,
        "match_quality": match_quality,
        "estimated_total_cost": estimated_cost,
        "platform_fee": platform_fee
    }


@app.post("/api/v1/protocol/verify")
def verify_agent(request: dict):
    """
    Mock verification endpoint - returns agent reputation data
    """
    agent_id = request.get("target_agent_id")
    
    # Find agent in test data
    agent_data = None
    for agent in TEST_AGENTS.values():
        if agent["agent_id"] == agent_id:
            agent_data = agent
            break
    
    if not agent_data:
        return {"verified": False, "error": "Agent not found"}
    
    return {
        "agent_id": agent_id,
        "verified": True,
        "reputation": {
            "score": agent_data["reputation_score"],
            "total_executions": 100,
            "successful_executions": int(100 * agent_data["success_rate"]),
            "success_rate": agent_data["success_rate"],
            "avg_response_time_ms": agent_data["avg_latency_ms"],
            "cost_accuracy": 0.98,
            "last_30_days": {}
        },
        "network_data": {
            "trust_level": "HIGH" if agent_data["reputation_score"] > 0.9 else "MEDIUM",
            "connected_agents": 25,
            "total_value_transacted": 5000.00
        },
        "proof_of_work": {
            "verification_hash": agent_data["agent_id"],
            "timestamp": datetime.now().isoformat()
        }
    }


@app.post("/api/v1/protocol/execute")
def execute_task(request: dict):
    """
    Mock execution endpoint - simulates task execution
    """
    executing_agent_id = request.get("executing_agent_id")
    capability = request.get("capability")
    input_data = request.get("input_data", {})
    
    execution_id = str(uuid.uuid4())
    
    # Simulate execution based on capability
    output_data = {}
    
    if capability == "math" or capability == "calculation":
        # Mock math result
        output_data = {
            "result": 425,
            "operation": "add",
            "inputs": input_data
        }
    elif capability == "translation":
        output_data = {
            "translated_text": "This is a mock translation result",
            "source_lang": "es",
            "target_lang": "en"
        }
    elif capability == "summarization":
        output_data = {
            "summary": "Mock summary: Key points extracted from input text."
        }
    elif capability == "validation":
        output_data = {
            "status": "PASS",
            "validation_rules_passed": ["completeness", "accuracy"]
        }
    else:
        output_data = {"result": "Mock execution completed"}
    
    return {
        "execution_id": execution_id,
        "status": "COMPLETED",
        "estimated_completion_ms": 250,
        "cost_final_usd": 0.10,
        "callback_registered": False,
        "output_data": output_data,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/protocol/settle")
def settle_payment(request: dict):
    """
    Mock settlement endpoint - simulates payment processing
    """
    execution_id = request.get("execution_id")
    payment_method = request.get("payment_method", "solana_usdc")
    
    return {
        "settlement_status": "SETTLED",
        "payment_tx_hash": f"mock_tx_{uuid.uuid4().hex[:16]}",
        "transaction_id": execution_id,
        "amounts": {
            "agent_payment_usd": 0.098,
            "platform_fee_usd": 0.002,
            "total_usd": 0.10
        },
        "reputation_updated": True,
        "on_chain_record": f"solana:mainnet:{uuid.uuid4().hex}",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("=" * 80)
    print("MOCK PROTOCOL SERVER - Agent Execution Protocol (AEP) Demo")
    print("=" * 80)
    print("\nStarting on http://localhost:8001")
    print("\nEndpoints:")
    print("  POST /api/v1/protocol/discover - Find agents by capability")
    print("  POST /api/v1/protocol/verify - Verify agent reputation")
    print("  POST /api/v1/protocol/execute - Execute task on agent")
    print("  POST /api/v1/protocol/settle - Settle payment")
    print("\nTest agents available:")
    for agent_key, agent_data in TEST_AGENTS.items():
        print(f"  - {agent_data['name']}: {agent_data['capabilities']}")
    print("\n" + "=" * 80)
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
