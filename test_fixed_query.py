"""
Test the fixed protocol discovery query with json to jsonb cast
"""

import psycopg2
import json

DATABASE_URL = "postgresql://postgres:aRFnDbaXZvAaIKFgFBnpjRmzoanlwGkO@mainline.proxy.rlwy.net:11716/railway"

print("Testing fixed protocol discovery query...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Test the fixed query with jsonb cast
capability = "math"
capability_condition = f"capabilities::jsonb @> '[\"{ capability}\"]'"

query = f"""
    SELECT 
        id, name, capabilities, quality_score
    FROM agents
    WHERE {capability_condition}
    AND is_active = true
    AND quality_score >= 50
    ORDER BY quality_score DESC
    LIMIT 10
"""

print(f"\nQuery:\n{query}\n")

try:
    cur.execute(query)
    matches = cur.fetchall()
    print(f"SUCCESS: Found {len(matches)} matching agents\n")
    
    for match in matches:
        caps = match[2] if isinstance(match[2], list) else []
        print(f"  - {match[1][:40]}")
        print(f"    Quality: {match[3]}, Capabilities: {caps[:5]}")
        
except Exception as e:
    print(f"ERROR: {e}")
    print(f"Error type: {type(e).__name__}")

conn.close()
print("\nDone.")
