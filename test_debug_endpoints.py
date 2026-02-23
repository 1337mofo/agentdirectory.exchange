"""
Test debug endpoints
"""
import requests
import json

BASE_URL = "https://agentdirectory.exchange"

print("[*] Testing rate limiting import...")
response = requests.get(f"{BASE_URL}/api/v1/debug/test-rate-limiting")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

print("\n[*] Testing registration flow...")
response = requests.post(f"{BASE_URL}/api/v1/debug/test-registration-flow")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
