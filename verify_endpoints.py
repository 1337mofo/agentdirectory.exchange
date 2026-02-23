"""
Verify new anti-abuse endpoints are available
"""
import requests

BASE_URL = "https://agentdirectory.exchange"

print("Verifying new endpoints are deployed...\n")

# Check OpenAPI docs for new endpoints
print("[*] Checking /openapi.json for new endpoints...")
response = requests.get(f"{BASE_URL}/openapi.json")

if response.status_code == 200:
    openapi = response.json()
    paths = openapi.get("paths", {})
    
    # Check for rate-limits endpoint
    if "/api/v1/agents/rate-limits" in paths:
        print("[OK] /api/v1/agents/rate-limits endpoint found")
    else:
        print("[ERROR] /api/v1/agents/rate-limits NOT FOUND")
    
    # Check for tool execution endpoint
    if "/api/v1/tools/{tool_id}/execute" in paths:
        print("[OK] /api/v1/tools/{tool_id}/execute endpoint found")
    else:
        print("[ERROR] /api/v1/tools/{tool_id}/execute NOT FOUND")
    
    # Check registration endpoint has updated description
    reg_endpoint = paths.get("/api/v1/agents/register", {})
    if "anti-abuse" in str(reg_endpoint).lower() or "rate limit" in str(reg_endpoint).lower():
        print("[OK] Registration endpoint has anti-abuse documentation")
    else:
        print("[WARN] Registration endpoint may not have updated docs")
else:
    print(f"[ERROR] Could not fetch OpenAPI docs: {response.status_code}")

print("\n[*] Testing /docs endpoint accessibility...")
response = requests.get(f"{BASE_URL}/docs")
if response.status_code == 200:
    print("[OK] API docs accessible at /docs")
else:
    print(f"[ERROR] Docs not accessible: {response.status_code}")

print("\n[INFO] Full test suite ready in test_anti_abuse_system.py")
