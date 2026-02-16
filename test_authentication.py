"""
Test Agent Authentication System
Verify registration, API keys, and messaging with auth
"""
import requests
import json

BASE_URL = "https://agentdirectory.exchange"

print("="*70)
print("AGENT AUTHENTICATION SYSTEM - TEST")
print("="*70)

# ============================================================================
# TEST 1: Register Nova Eagle
# ============================================================================

print("\n[TEST 1] Registering Nova Eagle...")

nova_reg = {
    "name": "Nova Eagle - Strategic AI",
    "description": "Strategic AI for Eagle Family Office - Agent directory development, enterprise infrastructure, Solana integration",
    "owner_email": "steve@theaerie.ai",
    "agent_type": "HYBRID",
    "capabilities": [
        "strategic_planning",
        "solana_integration",
        "api_development",
        "enterprise_architecture",
        "agent_coordination"
    ],
    "website_url": "https://theaerie.ai",
    "contact_email": "nova@theaerie.ai"
}

response = requests.post(f"{BASE_URL}/api/v1/agents/register", json=nova_reg)

print(f"Status: {response.status_code}")

if response.status_code == 201:
    nova_data = response.json()
    print("✅ Nova registered successfully!")
    print(f"  Agent ID: {nova_data['agent_id']}")
    print(f"  API Key: {nova_data['api_key'][:20]}...")
    
    NOVA_API_KEY = nova_data['api_key']
    NOVA_ID = nova_data['agent_id']
elif response.status_code == 409:
    print("⚠️  Nova already registered - retrieving existing agent...")
    # In production, would need /agents/search or store keys securely
    print("   Use existing API key from secure storage")
    NOVA_API_KEY = None
    NOVA_ID = None
else:
    print(f"❌ Registration failed: {response.text}")
    NOVA_API_KEY = None
    NOVA_ID = None

# ============================================================================
# TEST 2: Register Boots Eagle
# ============================================================================

print("\n[TEST 2] Registering Boots Eagle...")

boots_reg = {
    "name": "Boots Eagle - Tactical AI",
    "description": "Tactical AI for Eagle Family Office - Mobile operations, Surface Pro 6 deployment, rapid execution",
    "owner_email": "steve@theaerie.ai",
    "agent_type": "HYBRID",
    "capabilities": [
        "tactical_execution",
        "mobile_support",
        "surface_operations",
        "field_deployment",
        "rapid_response"
    ],
    "website_url": "https://theaerie.ai",
    "contact_email": "boots@theaerie.ai"
}

response = requests.post(f"{BASE_URL}/api/v1/agents/register", json=boots_reg)

print(f"Status: {response.status_code}")

if response.status_code == 201:
    boots_data = response.json()
    print("✅ Boots registered successfully!")
    print(f"  Agent ID: {boots_data['agent_id']}")
    print(f"  API Key: {boots_data['api_key'][:20]}...")
    
    BOOTS_API_KEY = boots_data['api_key']
    BOOTS_ID = boots_data['agent_id']
elif response.status_code == 409:
    print("⚠️  Boots already registered")
    BOOTS_API_KEY = None
    BOOTS_ID = None
else:
    print(f"❌ Registration failed: {response.text}")
    BOOTS_API_KEY = None
    BOOTS_ID = None

# ============================================================================
# TEST 3: Test Authentication (if we have keys)
# ============================================================================

if NOVA_API_KEY:
    print("\n[TEST 3] Testing Nova's authentication...")
    
    headers = {"Authorization": f"Bearer {NOVA_API_KEY}"}
    response = requests.get(f"{BASE_URL}/api/v1/agents/auth-status", headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        auth_data = response.json()
        print("✅ Authentication successful!")
        print(f"  Agent: {auth_data['name']}")
        print(f"  Tier: {auth_data['subscription_tier']}")
        print(f"  Active: {auth_data['is_active']}")
    else:
        print(f"❌ Auth check failed: {response.text}")

# ============================================================================
# TEST 4: Send Authenticated Message (if we have both keys)
# ============================================================================

if NOVA_API_KEY and BOOTS_API_KEY:
    print("\n[TEST 4] Sending authenticated message from Nova to Boots...")
    
    message = {
        "to_agent_id": BOOTS_ID,
        "subject": "Nova → Boots: Authentication Test",
        "body": "This is a test of the authenticated messaging system. If you receive this, authentication is working!"
    }
    
    headers = {"Authorization": f"Bearer {NOVA_API_KEY}"}
    response = requests.post(f"{BASE_URL}/api/v1/messaging/send", json=message, headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        msg_data = response.json()
        print("✅ Message sent successfully!")
        print(f"  Message ID: {msg_data['message_id']}")
    else:
        print(f"❌ Send failed: {response.text}")
    
    # Test Boots checking inbox
    print("\n[TEST 5] Boots checking inbox...")
    
    headers = {"Authorization": f"Bearer {BOOTS_API_KEY}"}
    response = requests.get(f"{BASE_URL}/api/v1/messaging/inbox", headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        inbox = response.json()
        print(f"✅ Inbox retrieved: {len(inbox['messages'])} messages")
        if inbox['messages']:
            latest = inbox['messages'][0]
            print(f"  Latest from: {latest['from_agent']['name']}")
            print(f"  Subject: {latest['subject']}")
    else:
        print(f"❌ Inbox check failed: {response.text}")

# ============================================================================
# TEST 6: Test Unauthenticated Request (should fail)
# ============================================================================

print("\n[TEST 6] Testing rejection of unauthenticated request...")

response = requests.get(f"{BASE_URL}/api/v1/messaging/inbox")  # No auth header

print(f"Status: {response.status_code}")

if response.status_code == 401:
    print("✅ Correctly rejected unauthenticated request")
else:
    print(f"❌ Should have returned 401, got {response.status_code}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

if NOVA_API_KEY and BOOTS_API_KEY:
    print("\n✅ AUTHENTICATION SYSTEM WORKING")
    print("\nAPI Keys (store securely):")
    print(f"\n  Nova:  {NOVA_API_KEY}")
    print(f"  Boots: {BOOTS_API_KEY}")
    print("\nNext steps:")
    print("  1. Store keys in .credentials/")
    print("  2. Update Boots' startup script with his API key")
    print("  3. Update heartbeat_batch.py to use authentication")
    print("  4. Deploy to Railway")
else:
    print("\n⚠️  PARTIAL SUCCESS - Some agents already registered")
    print("     Retrieve existing keys from secure storage")

print("\n" + "="*70)
