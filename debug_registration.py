"""
Debug registration endpoint error
"""
import requests
import json

BASE_URL = "https://agentdirectory.exchange"

print("[*] Testing registration endpoint with detailed error info...\n")

response = requests.post(
    f"{BASE_URL}/api/v1/agents/register",
    json={
        "name": "DebugTestAgent",
        "description": "Testing anti-abuse registration",
        "owner_email": "debug@example.com",
        "agent_type": "HYBRID"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}\n")

try:
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except:
    print("Response Text:")
    print(response.text)
