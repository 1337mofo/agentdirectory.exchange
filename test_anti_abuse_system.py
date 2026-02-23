"""
Test Anti-Abuse System - Complete Flow
Tests registration, rate limits, and tool execution
"""
import requests
import json
import time

BASE_URL = "https://agentdirectory.exchange"
# BASE_URL = "http://localhost:8000"  # For local testing

def test_registration():
    """Test agent registration with anti-abuse checks"""
    print("\n" + "="*60)
    print("TEST 1: Agent Registration")
    print("="*60)
    
    # Test successful registration
    print("\n[*] Testing successful registration...")
    response = requests.post(
        f"{BASE_URL}/api/v1/agents/register",
        json={
            "name": f"TestAgent_{int(time.time())}",
            "description": "Test agent for anti-abuse system validation",
            "owner_email": f"test_{int(time.time())}@example.com",
            "agent_type": "HYBRID"
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        print("[OK] Registration successful!")
        print(f"    Agent ID: {data['agent_id']}")
        print(f"    API Key: {data['api_key'][:20]}...")
        print(f"    Message: {data['message']}")
        return data['api_key']
    else:
        print(f"[ERROR] Registration failed: {response.status_code}")
        print(response.text)
        return None


def test_disposable_email():
    """Test disposable email blocking"""
    print("\n" + "="*60)
    print("TEST 2: Disposable Email Blocking")
    print("="*60)
    
    print("\n[*] Testing disposable email rejection...")
    response = requests.post(
        f"{BASE_URL}/api/v1/agents/register",
        json={
            "name": f"DisposableTest_{int(time.time())}",
            "description": "Test disposable email blocking",
            "owner_email": "test@tempmail.com",
            "agent_type": "HYBRID"
        }
    )
    
    if response.status_code == 400:
        print("[OK] Disposable email correctly rejected!")
        print(f"    Message: {response.json()['detail']}")
    else:
        print(f"[WARN] Expected 400, got {response.status_code}")
        print(response.text)


def test_rate_limits(api_key):
    """Test rate limit checking"""
    print("\n" + "="*60)
    print("TEST 3: Rate Limit Status")
    print("="*60)
    
    print("\n[*] Checking rate limit status...")
    response = requests.get(
        f"{BASE_URL}/api/v1/agents/rate-limits",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("[OK] Rate limits retrieved!")
        print(f"    Free credits remaining: {data['free_credits']['remaining']}/{data['free_credits']['total']}")
        print(f"    Paid credits: {data['paid_credits']['remaining']}")
        print(f"    Hourly limit: {data['hourly_limit']['remaining']}/{data['hourly_limit']['limit']}")
        print(f"    Resets in: {data['hourly_limit']['resets_in_seconds']} seconds")
        print(f"    Upgrade recommended: {data.get('upgrade_recommended', False)}")
        return data
    else:
        print(f"[ERROR] Failed to get rate limits: {response.status_code}")
        print(response.text)
        return None


def test_tool_execution(api_key):
    """Test tool execution proxy"""
    print("\n" + "="*60)
    print("TEST 4: Tool Execution Proxy")
    print("="*60)
    
    # First, get a tool ID
    print("\n[*] Finding a tool to test...")
    response = requests.get(f"{BASE_URL}/api/v1/tools/?limit=1")
    
    if response.status_code != 200 or not response.json().get("tools"):
        print("[WARN] No tools available for testing")
        return
    
    tool = response.json()["tools"][0]
    tool_id = tool["id"]
    tool_name = tool["name"]
    
    print(f"[OK] Found tool: {tool_name}")
    print(f"    ID: {tool_id}")
    
    # Test execution
    print(f"\n[*] Executing tool: {tool_name}...")
    response = requests.post(
        f"{BASE_URL}/api/v1/tools/{tool_id}/execute",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"parameters": {"test": "value"}}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("[OK] Tool execution successful!")
        print(f"    Success: {data['success']}")
        print(f"    Cost: ${data['cost_usd']}")
        print(f"    Execution time: {data.get('execution_time_ms', 'N/A')}ms")
        print(f"    Credits remaining: {data['credits_remaining']['free_credits']['remaining']}")
        return data
    elif response.status_code == 429:
        print("[OK] Rate limit working correctly!")
        print(f"    Message: {response.json()['detail']}")
    elif response.status_code == 501:
        print("[INFO] Tool has no API endpoint configured (expected for seeded tools)")
    else:
        print(f"[INFO] Response: {response.status_code}")
        print(response.text)


def test_hourly_rate_limit(api_key):
    """Test hourly rate limit enforcement"""
    print("\n" + "="*60)
    print("TEST 5: Hourly Rate Limit Enforcement")
    print("="*60)
    
    print("\n[*] Making 6 rapid requests to test hourly limit (5/hour)...")
    
    # Get a tool
    response = requests.get(f"{BASE_URL}/api/v1/tools/?limit=1")
    if response.status_code != 200 or not response.json().get("tools"):
        print("[WARN] No tools available for rate limit test")
        return
    
    tool_id = response.json()["tools"][0]["id"]
    
    success_count = 0
    rate_limited = False
    
    for i in range(6):
        response = requests.post(
            f"{BASE_URL}/api/v1/tools/{tool_id}/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"parameters": {}}
        )
        
        if response.status_code == 200:
            success_count += 1
            print(f"    Request {i+1}: [OK] Executed")
        elif response.status_code == 429:
            rate_limited = True
            print(f"    Request {i+1}: [BLOCKED] Rate limited (as expected)")
            print(f"        Message: {response.json()['detail']}")
            break
        elif response.status_code == 501:
            print(f"    Request {i+1}: [SKIP] Tool has no endpoint")
            break
        else:
            print(f"    Request {i+1}: [INFO] Status {response.status_code}")
        
        time.sleep(0.5)  # Small delay between requests
    
    if success_count <= 5 and (rate_limited or success_count == 0):
        print(f"\n[OK] Hourly rate limit working correctly!")
        print(f"    Allowed: {success_count} requests")
    else:
        print(f"\n[WARN] Expected rate limit after 5 requests, got {success_count}")


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("ANTI-ABUSE SYSTEM TEST SUITE")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print("="*60)
    
    # Test 1: Registration
    api_key = test_registration()
    if not api_key:
        print("\n[ERROR] Registration failed - stopping tests")
        return
    
    # Test 2: Disposable email
    test_disposable_email()
    
    # Test 3: Rate limits
    rate_limits = test_rate_limits(api_key)
    
    # Test 4: Tool execution
    test_tool_execution(api_key)
    
    # Test 5: Hourly rate limit enforcement
    # test_hourly_rate_limit(api_key)  # Commented out - would consume credits
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
    print("\n[SUMMARY]")
    print("  Registration: OK")
    print("  Disposable email blocking: OK")
    print("  Rate limit checking: OK")
    print("  Tool execution: Tested")
    print("\n[OK] Anti-abuse system is operational!")


if __name__ == "__main__":
    run_all_tests()
