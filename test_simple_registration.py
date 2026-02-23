"""
Test simple agent registration
"""
import requests
import json
import time

BASE_URL = "https://agentdirectory.exchange"

# Try minimal registration
data = {
    "name": f"MinimalTest_{int(time.time())}",
    "description": "Minimal test agent with just required fields",
    "owner_email": "minimal@example.com"
}

print("[*] Testing minimal registration...")
print(f"Request: {json.dumps(data, indent=2)}")

response = requests.post(
    f"{BASE_URL}/api/v1/agents/register",
    json=data,
    headers={"Content-Type": "application/json"}
)

print(f"\nStatus: {response.status_code}")
print(f"Headers: {dict(response.headers)}")

try:
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
except:
    print(f"\nRaw response:")
    print(response.text)
