"""
Deploy Agents to Railway Database - FIXED for Railway Schema
Matches actual Railway columns exactly
"""

import json
import os
import psycopg2
import uuid
from datetime import datetime

DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

print("="*60)
print("AGENT DEPLOYMENT - RAILWAY SCHEMA COMPATIBLE")
print("="*60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Load agents
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "discovered_agents_v2.jsonl")
agents = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        agent = json.loads(line)
        if agent.get("evaluation_score", 0) >= 40:  # Lower threshold
            agents.append(agent)

print(f"\n[INFO] Loaded {len(agents)} agents from {input_file}")

# Connect to database
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
print("[INFO] Connected to Railway database")

# Deploy agents
deployed = 0
skipped = 0
failed = 0

for agent in agents:
    try:
        # Check if exists
        cur.execute(
            "SELECT id FROM agents WHERE source_url = %s",
            (agent["source_url"],)
        )
        
        if cur.fetchone():
            skipped += 1
            continue
        
        # Insert with Railway schema columns
        agent_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO agents (
                id,
                name,
                description,
                source_url,
                agent_type,
                capabilities,
                verification_status,
                is_active,
                rating_avg,
                quality_score,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s::json, %s, %s, %s, %s, NOW(), NOW()
            )
            RETURNING id
        """, (
            agent_id,
            agent["name"][:255],
            agent.get("description", "AI agent")[:1000],
            agent["source_url"],
            "CAPABILITY",  # From Railway enum
            json.dumps({"tags": ["general_ai"]}),  # JSON format
            "UNVERIFIED",  # From Railway enum
            True,
            0.0,
            agent.get("evaluation_score", 50)
        ))
        
        agent_id = cur.fetchone()[0]
        deployed += 1
        
        # Commit every 50 agents
        if deployed % 50 == 0:
            conn.commit()
            print(f"[PROGRESS] Deployed {deployed} agents...")
    
    except Exception as e:
        failed += 1
        if failed < 10:  # Only show first 10 errors
            print(f"[WARNING] Failed to deploy {agent['name']}: {e}")
        continue

# Final commit
conn.commit()

print("\n" + "="*60)
print(f"DEPLOYMENT COMPLETE")
print("="*60)
print(f"✅ Deployed: {deployed}")
print(f"⏭️ Skipped (already exists): {skipped}")
print(f"❌ Failed: {failed}")
print(f"\n[TOTAL] {deployed + skipped} agents now in database")
print("="*60)

# Verify count
cur.execute("SELECT COUNT(*) FROM agents")
total = cur.fetchone()[0]
print(f"\n[DATABASE] Total agent count: {total}")

conn.close()
