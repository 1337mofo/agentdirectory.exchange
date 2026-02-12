"""
Deploy Crawler Agents to Production - FIXED for actual schema
Works with the Agent model in backend/models/agent.py
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
    print("[ERROR] psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Get DATABASE_URL from environment or argument
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL and len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not provided.")
    print("Usage: python deploy_agents_fixed.py [DATABASE_URL]")
    sys.exit(1)

def deploy_agents():
    """Deploy discovered agents to production database"""
    
    # Try V2 (aggressive) first, fall back to V1
    input_file = "discovered_agents_v2.jsonl" if os.path.exists("discovered_agents_v2.jsonl") else "discovered_agents.jsonl"
    
    if not os.path.exists(input_file):
        print("[ERROR] No discovered agents file found. Run crawler first.")
        return 0
    
    print("="*60)
    print("AGENT DEPLOYMENT - PRODUCTION")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"[INFO] Using input file: {input_file}")
    
    # Load agents
    agents = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                agent = json.loads(line)
                # Quality threshold
                if agent.get("evaluation_score", 0) >= 40:  # Lower threshold for more agents
                    agents.append(agent)
            except:
                continue
    
    print(f"[INFO] Found {len(agents)} high-quality agents to deploy")
    print()
    
    # Connect to database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print(f"[INFO] Connected to database")
        print()
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return 0
    
    # Deploy agents
    deployed = 0
    skipped = 0
    failed = 0
    
    for i, agent in enumerate(agents, 1):
        try:
            agent_name = agent["name"][:255]
            
            # Check if agent already exists (by name)
            cur.execute(
                "SELECT id FROM agents WHERE name = %s",
                (agent_name,)
            )
            
            if cur.fetchone():
                skipped += 1
                continue
            
            # Prepare data
            agent_id = uuid.uuid4()
            api_key = f"sk_{uuid.uuid4().hex}"
            
            # Insert agent with correct schema
            cur.execute("""
                INSERT INTO agents (
                    id,
                    name,
                    description,
                    agent_type,
                    owner_email,
                    api_key,
                    is_active,
                    capabilities,
                    pricing_model,
                    rating_avg,
                    rating_count,
                    transaction_count,
                    revenue_total_usd,
                    quality_score,
                    success_rate,
                    verification_status,
                    subscription_tier,
                    rate_limit_per_hour,
                    extra_data,
                    created_at,
                    updated_at,
                    last_active_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
                )
            """, (
                agent_id,
                agent_name,
                agent.get("description", "AI agent discovered via marketplace crawler")[:500],
                "CAPABILITY",  # agent_type (uppercase for database enum)
                "marketplace@agentdirectory.exchange",  # owner_email (unclaimed agents)
                api_key,
                True,  # is_active
                Json(["general_ai", "automated"]),  # capabilities
                Json({"per_query": 5.00}),  # pricing_model
                0.0,  # rating_avg
                0,  # rating_count
                0,  # transaction_count
                0.0,  # revenue_total_usd
                agent.get("evaluation_score", 50),  # quality_score
                1.0,  # success_rate
                "UNVERIFIED",  # verification_status (uppercase for database enum)
                "free",  # subscription_tier
                100,  # rate_limit_per_hour
                Json({
                    "source_url": agent.get("source_url", ""),
                    "source_type": agent.get("source", "crawler"),
                    "discovered_at": datetime.now().isoformat(),
                    "original_data": {
                        "downloads": agent.get("downloads"),
                        "likes": agent.get("likes"),
                        "language": agent.get("language")
                    }
                })
            ))
            
            deployed += 1
            
            # Progress indicator
            if i % 50 == 0:
                print(f"[PROGRESS] {i}/{len(agents)} agents processed ({deployed} deployed, {skipped} skipped)")
            
        except Exception as e:
            failed += 1
            if failed < 5:  # Only show first few errors
                print(f"[WARNING] Failed to deploy {agent.get('name', 'unknown')}: {str(e)[:100]}")
            continue
    
    # Commit all changes
    conn.commit()
    cur.close()
    conn.close()
    
    print()
    print("="*60)
    print(f"DEPLOYMENT COMPLETE")
    print("="*60)
    print(f"✓ Deployed: {deployed} agents")
    print(f"⊘ Skipped: {skipped} agents (already exist)")
    print(f"✗ Failed: {failed} agents")
    print(f"→ Total in database: {deployed + skipped} agents")
    print()
    
    return deployed

if __name__ == "__main__":
    deployed_count = deploy_agents()
    sys.exit(0 if deployed_count > 0 else 1)
