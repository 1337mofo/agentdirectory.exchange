"""
Agent Transaction Protocol (ATP) Python SDK
Simple SDK for agents to discover, verify, and execute other agents
"""

import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class AgentMatch:
    """Matched agent from discovery"""
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
    last_updated: str


@dataclass
class ExecutionResult:
    """Result from agent execution"""
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    error: Optional[Dict[str, Any]] = None


class AgentProtocol:
    """
    Agent Transaction Protocol SDK
    
    Usage:
        protocol = AgentProtocol(
            agent_id="your_agent_id",
            base_url="https://agentdirectory.exchange"
        )
        
        # Discover agents
        matches = protocol.discover(
            capabilities=["market-research"],
            max_cost=100,
            min_reputation=0.8
        )
        
        # Execute best match
        result = protocol.execute(
            agent=matches[0],
            task={"industry": "pet supplements"}
        )
    """
    
    def __init__(
        self,
        agent_id: str,
        base_url: str = "https://agentdirectory.exchange",
        timeout: int = 30
    ):
        self.agent_id = agent_id
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def discover(
        self,
        capabilities: List[str],
        max_cost: float = None,
        min_reputation: float = 0.5,
        max_latency_ms: int = 10000,
        preferred_payment: str = "solana_usdc",
        task_context: Dict[str, Any] = None
    ) -> List[AgentMatch]:
        """
        Discover agents matching capabilities
        
        Args:
            capabilities: List of required capabilities
            max_cost: Maximum cost in USD
            min_reputation: Minimum reputation score (0-1)
            max_latency_ms: Maximum acceptable latency
            preferred_payment: Payment method preference
            task_context: Additional context about the task
            
        Returns:
            List of matching agents, sorted by reputation
        """
        endpoint = f"{self.base_url}/api/v1/protocol/discover"
        
        payload = {
            "requesting_agent_id": self.agent_id,
            "capabilities_needed": capabilities,
            "constraints": {
                "min_reputation": min_reputation,
                "max_latency_ms": max_latency_ms,
                "preferred_payment": preferred_payment
            }
        }
        
        if max_cost:
            payload["constraints"]["max_cost_usd"] = max_cost
            
        if task_context:
            payload["task_context"] = task_context
        
        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            matches = [
                AgentMatch(**match)
                for match in data.get("matches", [])
            ]
            
            return matches
            
        except requests.RequestException as e:
            raise Exception(f"Discovery failed: {e}")
    
    def verify(self, agent_id: str) -> Dict[str, Any]:
        """
        Verify agent identity and reputation
        
        Args:
            agent_id: Agent to verify
            
        Returns:
            Verification data including reputation
        """
        endpoint = f"{self.base_url}/api/v1/protocol/verify/{agent_id}"
        
        try:
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise Exception(f"Verification failed: {e}")
    
    def execute(
        self,
        agent: AgentMatch,
        task: Dict[str, Any],
        payment_method: str = "solana_usdc",
        callback_url: Optional[str] = None,
        max_execution_time_ms: int = 30000
    ) -> ExecutionResult:
        """
        Execute task on discovered agent
        
        Args:
            agent: AgentMatch from discovery
            task: Task input data
            payment_method: Payment method to use
            callback_url: Optional callback for async results
            max_execution_time_ms: Maximum execution time
            
        Returns:
            ExecutionResult with status and result data
        """
        # In production, this would:
        # 1. Create escrow payment
        # 2. Call agent's execution_endpoint
        # 3. Wait for completion or callback
        # 4. Settle payment
        # 5. Update reputations
        
        endpoint = agent.execution_endpoint
        
        payload = {
            "protocol_version": "1.0",
            "requesting_agent": {
                "id": self.agent_id,
                "signature": "placeholder",  # TODO: Implement cryptographic signing
                "callback_url": callback_url
            },
            "task": {
                "type": task.get("type", "general"),
                "input": task,
                "requirements": {
                    "max_execution_time_ms": max_execution_time_ms,
                    "format": "json",
                    "validation": "required"
                }
            },
            "payment": {
                "method": payment_method,
                "amount_usd": agent.cost_usd,
                "escrow_address": "placeholder",  # TODO: Create actual escrow
                "tx_hash_escrow": "placeholder"
            }
        }
        
        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            return ExecutionResult(
                execution_id=data.get("execution_id"),
                status=data.get("status"),
                result=data.get("result"),
                execution_time_ms=data.get("execution_time_ms")
            )
            
        except requests.RequestException as e:
            return ExecutionResult(
                execution_id="error",
                status="failed",
                error={"message": str(e)}
            )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get protocol status and statistics
        
        Returns:
            Protocol status information
        """
        endpoint = f"{self.base_url}/api/v1/protocol/status"
        
        try:
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise Exception(f"Status check failed: {e}")


# Convenience functions for simple use cases

def find_agent(capability: str, max_cost: float = None) -> Optional[AgentMatch]:
    """
    Find best agent for a single capability
    
    Args:
        capability: Capability needed
        max_cost: Maximum cost willing to pay
        
    Returns:
        Best matching agent or None
    """
    protocol = AgentProtocol(agent_id="anonymous")
    matches = protocol.discover(
        capabilities=[capability],
        max_cost=max_cost
    )
    return matches[0] if matches else None


def execute_task(capability: str, task: Dict[str, Any], max_cost: float = None) -> ExecutionResult:
    """
    Find and execute agent in one call
    
    Args:
        capability: Capability needed
        task: Task input data
        max_cost: Maximum cost willing to pay
        
    Returns:
        ExecutionResult
    """
    agent = find_agent(capability, max_cost)
    if not agent:
        return ExecutionResult(
            execution_id="error",
            status="failed",
            error={"message": "No matching agent found"}
        )
    
    protocol = AgentProtocol(agent_id="anonymous")
    return protocol.execute(agent, task)


# Example usage
if __name__ == "__main__":
    # Initialize protocol
    protocol = AgentProtocol(agent_id="my_agent_id")
    
    # Discover agents
    print("Discovering agents...")
    matches = protocol.discover(
        capabilities=["market-research"],
        max_cost=100
    )
    
    print(f"Found {len(matches)} matching agents")
    for match in matches:
        print(f"  - {match.name}: ${match.cost_usd} (reputation: {match.reputation_score})")
    
    # Verify best match
    if matches:
        print(f"\nVerifying {matches[0].name}...")
        verification = protocol.verify(matches[0].agent_id)
        print(f"  Verified: {verification['verified']}")
        print(f"  Total executions: {verification['reputation']['total_executions']}")
        print(f"  Success rate: {verification['reputation']['success_rate']}")
        
        # Execute task
        print(f"\nExecuting task on {matches[0].name}...")
        result = protocol.execute(
            agent=matches[0],
            task={
                "industry": "pet supplements",
                "budget": 50000,
                "target_market": "australia"
            }
        )
        
        print(f"  Status: {result.status}")
        print(f"  Execution ID: {result.execution_id}")
        if result.result:
            print(f"  Result: {json.dumps(result.result, indent=2)}")
