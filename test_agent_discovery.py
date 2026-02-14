"""
Test Agent Discovery Protocol
Shows agents finding each other by capability
"""
import requests
import json

BASE_URL = "https://agentdirectory.exchange"

def test_discovery():
    """Test agent discovery endpoint"""
    print("=" * 60)
    print("TESTING AGENT DISCOVERY PROTOCOL")
    print("=" * 60)
    
    # Discover agents with translation capability
    discover_request = {
        "requesting_agent_id": "test-orchestrator-001",
        "capabilities_needed": ["translation", "language"],
        "constraints": {
            "max_price_usd": 5.0,
            "response_time_max_seconds": 30
        }
    }
    
    print("\n[REQUEST] Finding agents with translation capability...")
    print(json.dumps(discover_request, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/protocol/discover",
            json=discover_request,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            print(f"\n[SUCCESS] Found {len(matches)} matching agents:")
            for i, agent in enumerate(matches[:5], 1):
                print(f"\n  Agent {i}:")
                print(f"    Name: {agent.get('name')}")
                print(f"    ID: {agent.get('agent_id')}")
                print(f"    Capabilities: {', '.join(agent.get('capabilities', []))}")
                print(f"    Price: ${agent.get('pricing', {}).get('price_usd', 0)}")
                print(f"    Reputation: {agent.get('reputation_score', 0)}/100")
        else:
            print(f"\n[ERROR] Discovery failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n[ERROR] Request failed: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_discovery()
