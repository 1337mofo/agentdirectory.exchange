"""
Deploy Crawler to Production - Direct Database Insert
Uses Railway DATABASE_URL from environment or command line
"""

import json
import os
import sys
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("[ERROR] psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Get DATABASE_URL from environment or argument
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL and len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL not provided.")
    print("Usage: python deploy_crawler_production.py [DATABASE_URL]")
    print("   or: export DATABASE_URL=your-database-url && python deploy_crawler_production.py")
    sys.exit(1)

def deploy_agents():
    """Deploy discovered agents to production database"""
    
    # Read discovered agents
    if not os.path.exists("discovered_agents.jsonl"):
        print("[ERROR] discovered_agents.jsonl not found. Run agent_discovery_crawler.py first.")
        return 0
    
    agents = []
    with open("discovered_agents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            agent = json.loads(line)
            if agent.get("evaluation_score", 0) >= 50:  # Quality threshold
                agents.append(agent)
    
    print(f"[INFO] Found {len(agents)} high-quality agents to deploy")
    
    # Connect to database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print(f"[INFO] Connected to database")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return 0
    
    # Deploy agents
    deployed = 0
    skipped = 0
    
    for agent in agents:
        try:
            # Check if agent already exists
            cur.execute(
                "SELECT id FROM agents WHERE source_url = %s",
                (agent["source_url"],)
            )
            
            if cur.fetchone():
                skipped += 1
                continue
            
            # Insert agent
            cur.execute("""
                INSERT INTO agents (
                    name,
                    description,
                    source_url,
                    agent_type,
                    capabilities,
                    verified,
                    is_active,
                    rating_avg,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING id
            """, (
                agent["name"][:255],  # Truncate if too long
                agent["description"][:500] if agent.get("description") else "AI agent",
                agent["source_url"],
                "general",  # Default type
                ["general_ai"],  # Default capabilities as array
                False,  # Unverified until owner claims
                True,  # Active
                0.0  # No ratings yet
            ))
            
            agent_id = cur.fetchone()[0]
            
            # Create default listing
            cur.execute("""
                INSERT INTO listings (
                    seller_agent_id,
                    title,
                    description,
                    listing_type,
                    category,
                    price_usd,
                    pricing_model,
                    status,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """, (
                agent_id,
                f"{agent['name']} - AI Agent Service",
                agent["description"][:500] if agent.get("description") else "AI agent service",
                "capability",
                "ai_services",
                5.00,  # Default $5 per use
                "per_use",
                "active"
            ))
            
            deployed += 1
            
            if deployed % 10 == 0:
                print(f"[INFO] Deployed {deployed} agents...")
                conn.commit()  # Commit every 10 agents
        
        except Exception as e:
            print(f"[WARNING] Failed to deploy {agent.get('name')}: {e}")
            conn.rollback()
    
    # Final commit
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n[SUCCESS] Deployed {deployed} agents")
    print(f"[INFO] Skipped {skipped} duplicates")
    
    return deployed


if __name__ == "__main__":
    print("=" * 60)
    print("AGENT CRAWLER - PRODUCTION DEPLOYMENT")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    deployed = deploy_agents()
    
    print()
    print("=" * 60)
    print(f"DEPLOYMENT COMPLETE - {deployed} agents live")
    print("=" * 60)
