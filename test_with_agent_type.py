"""
Test registration with agent_type
"""
import requests
import json
import time

BASE_URL = "https://agentdirectory.exchange"

data = {
    "name": f"TypeTest_{int(time.time())}",
    "description": "Test agent with agent_type specified",
    "owner_email": f"typetest_{int(time.time())}@example.com",
    "agent_type": "HYBRID"
}

print("[*] Testing registration with agent_type...")
print(f"Request: {json.dumps(data, indent=2)}")

response = requests.post(
    f"{BASE_URL}/api/v1/agents/register",
    json=data
)

print(f"\nStatus: {response.status_code}")

try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)
