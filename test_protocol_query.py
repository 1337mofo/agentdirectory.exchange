"""
Test the protocol discovery query to see what's failing
"""

import psycopg2
import json

DATABASE_URL = "postgresql://postgres:aRFnDbaXZvAaIKFgFBnpjRmzoanlwGkO@mainline.proxy.rlwy.net:11716/railway"

print("Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Test 1: Check if any agents exist
print("\n1. Checking total agent count...")
cur.execute("SELECT COUNT(*) FROM agents")
total = cur.fetchone()[0]
print(f"   Total agents: {total}")

# Test 2: Check active agents
print("\n2. Checking active agent count...")
cur.execute("SELECT COUNT(*) FROM agents WHERE is_active = true")
active = cur.fetchone()[0]
print(f"   Active agents: {active}")

# Test 3: Check agents with capabilities
print("\n3. Checking agents with non-null capabilities...")
cur.execute("SELECT COUNT(*) FROM agents WHERE capabilities IS NOT NULL")
with_caps = cur.fetchone()[0]
print(f"   Agents with capabilities: {with_caps}")

# Test 4: Sample some capabilities
print("\n4. Sampling agent capabilities...")
cur.execute("SELECT id, name, capabilities FROM agents WHERE capabilities IS NOT NULL LIMIT 5")
rows = cur.fetchall()
for row in rows:
    caps = row[2] if isinstance(row[2], list) else (json.loads(row[2]) if row[2] else [])
    print(f"   {row[1][:30]}: {caps[:3] if len(caps) > 3 else caps}")

# Test 5: Try the actual protocol query
print("\n5. Testing protocol discovery query for 'math' capability...")
capability = "math"
capability_condition = f'capabilities @> \'"{capability}"\''

query = f"""
    SELECT 
        id, name, capabilities
    FROM agents
    WHERE {capability_condition}
    AND is_active = true
    LIMIT 5
"""

print(f"   Query: {query}")

try:
    cur.execute(query)
    matches = cur.fetchall()
    print(f"   Found {len(matches)} matches")
    for match in matches:
        print(f"     - {match[1]}")
except Exception as e:
    print(f"   ERROR: {e}")
    print(f"   Error type: {type(e).__name__}")

# Test 6: Try alternative query with JSONB cast
print("\n6. Testing with JSONB cast...")
query_with_cast = """
    SELECT 
        id, name, capabilities
    FROM agents
    WHERE capabilities::jsonb @> '["math"]'
    AND is_active = true
    LIMIT 5
"""

try:
    cur.execute(query_with_cast)
    matches = cur.fetchall()
    print(f"   Found {len(matches)} matches")
    for match in matches:
        caps = match[2] if isinstance(match[2], list) else (json.loads(match[2]) if match[2] else [])
        print(f"     - {match[1]}: {caps}")
except Exception as e:
    print(f"   ERROR: {e}")

conn.close()
print("\nDone.")
