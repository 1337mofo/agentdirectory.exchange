"""
Deploy Crawler Agents to Production - BATCH COMMIT VERSION
Commits every 50 agents to prevent rollback on error
"""

import json
import os
import sys
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import Json
    from psycopg2.extensions import register_adapter, AsIs
    import uuid
    
    # Register UUID adapter
    def adapt_uuid(val):
        return AsIs(f"'{val}'::uuid")
    
    register_adapter(uuid.UUID, adapt_uuid)
    
except ImportError:
    print("[ERROR] psycopg2 not installed.")
    sys.exit(1)

# Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL and len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not provided.")
    sys.exit(1)

def deploy_agents():
    """Deploy discovered agents with batch commits"""
    
    input_file = "discovered_agents_v2.jsonl" if os.path.exists("discovered_agents_v2.jsonl") else "discovered_agents.jsonl"
    
    if not os.path.exists(input_file):
        print("[ERROR] No discovered agents file found.")
        return 0
    
    print("="*60)
    print("AGENT DEPLOYMENT - PRODUCTION (BATCH COMMIT)")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"[INFO] Using input file: {input_file}")
    
    # Load agents
    agents = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                agent = json.loads(line)
                if agent.get("evaluation_score", 0) >= 40:
                    agents.append(agent)
            except:
                continue
    
    print(f"[INFO] Found {len(agents)} high-quality agents to deploy\n")
    
    # Connect to database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Manual transaction control
        cur = conn.cursor()
        print(f"[INFO] Connected to database\n")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return 0
    
    # Deploy agents with batch commits
    deployed = 0
    skipped = 0
    failed = 0
    batch_size = 50
    
    for i, agent in enumerate(agents, 1):
        try:
            agent_name = agent["name"][:255]
            
            # Check if exists
            cur.execute("SELECT id FROM agents WHERE name = %s", (agent_name,))
            
            if cur.fetchone():
                skipped += 1
                continue
            
            # Prepare data
            agent_id = uuid.uuid4()
            api_key = f"sk_{uuid.uuid4().hex}"
            
            # Insert agent
            cur.execute("""
                INSERT INTO agents (
                    id, name, description, agent_type, owner_email, api_key,
                    is_active, capabilities, pricing_model, rating_avg, rating_count,
                    transaction_count, revenue_total_usd, quality_score, success_rate,
                    verification_status, subscription_tier, rate_limit_per_hour,
                    extra_data, created_at, updated_at, last_active_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    NOW(), NOW(), NOW()
                )
            """, (
                agent_id,
                agent_name,
                agent.get("description", "AI agent")[:500],
                "CAPABILITY",
                "marketplace@agentdirectory.exchange",
                api_key,
                True,
                Json(["general_ai", "automated"]),
                Json({"per_query": 5.00}),
                0.0, 0, 0, 0.0,
                agent.get("evaluation_score", 50),
                1.0,
                "UNVERIFIED",
                "free",
                100,
                Json({
                    "source_url": agent.get("source_url", ""),
                    "source_type": agent.get("source", "crawler"),
                    "discovered_at": datetime.now().isoformat()
                })
            ))
            
            deployed += 1
            
            # Commit every batch_size agents
            if deployed % batch_size == 0:
                conn.commit()
                print(f"[COMMIT] Batch committed: {deployed} agents deployed so far")
            
            # Progress indicator
            if i % 50 == 0:
                print(f"[PROGRESS] {i}/{len(agents)} agents processed ({deployed} deployed, {skipped} skipped)")
            
        except Exception as e:
            failed += 1
            if failed < 3:
                print(f"[WARNING] Failed to deploy {agent.get('name', 'unknown')}: {str(e)[:100]}")
            continue
    
    # Final commit for remaining agents
    try:
        conn.commit()
        print(f"[COMMIT] Final batch committed\n")
    except Exception as e:
        print(f"[ERROR] Final commit failed: {e}")
    
    cur.close()
    conn.close()
    
    print("="*60)
    print(f"DEPLOYMENT COMPLETE")
    print("="*60)
    print(f"Deployed: {deployed} agents")
    print(f"Skipped: {skipped} agents (duplicates)")
    print(f"Failed: {failed} agents")
    print(f"Total in database: {deployed} agents")
    print()
    
    return deployed

if __name__ == "__main__":
    deployed_count = deploy_agents()
    sys.exit(0 if deployed_count > 0 else 1)
