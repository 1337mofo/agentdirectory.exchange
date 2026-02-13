"""
Continuous Agent Crawler for Creative XR Labs Server
Discovers agents from multiple sources and deploys to Railway DB
Runs every hour via cron job
"""

import json
import os
import sys
import uuid
import psycopg2
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Railway Database Connection
DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

# Configuration
QUALITY_THRESHOLD = 40  # Lower for more agents
AGENTS_PER_RUN = 100    # Discover 100 per run
LOG_FILE = "/home/nova/crawler.log"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")
    except:
        pass

def crawl_huggingface_spaces(limit=50):
    """Crawl HuggingFace Spaces for AI agents"""
    agents = []
    
    try:
        # Get trending spaces
        url = "https://huggingface.co/api/spaces"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            spaces = response.json()[:limit]
            
            for space in spaces:
                agent = {
                    "source": "huggingface_spaces",
                    "source_id": space.get("id", ""),
                    "name": space.get("id", "").split("/")[-1].replace("-", " ").title(),
                    "description": space.get("description", "AI application from HuggingFace"),
                    "source_url": f"https://huggingface.co/spaces/{space.get('id', '')}",
                    "metrics": {
                        "likes": space.get("likes", 0)
                    },
                    "capabilities": ["ai_application"],
                    "discovered_at": datetime.now().isoformat(),
                    "evaluation_score": min(100, 50 + space.get("likes", 0) // 10)
                }
                
                if agent["evaluation_score"] >= QUALITY_THRESHOLD:
                    agents.append(agent)
        
        log(f"Discovered {len(agents)} agents from HuggingFace")
    
    except Exception as e:
        log(f"ERROR crawling HuggingFace: {e}")
    
    return agents

def crawl_github_ai(limit=30):
    """Crawl GitHub for AI agent repositories"""
    agents = []
    
    try:
        # Search for AI agent repos
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "ai agent OR llm agent",
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            repos = response.json().get("items", [])
            
            for repo in repos:
                agent = {
                    "source": "github",
                    "source_id": repo["full_name"],
                    "name": repo["name"].replace("-", " ").title(),
                    "description": repo.get("description", "AI agent from GitHub"),
                    "source_url": repo["html_url"],
                    "metrics": {
                        "stars": repo.get("stargazers_count", 0)
                    },
                    "capabilities": ["ai_application"],
                    "discovered_at": datetime.now().isoformat(),
                    "evaluation_score": min(100, 40 + repo.get("stargazers_count", 0) // 100)
                }
                
                if agent["evaluation_score"] >= QUALITY_THRESHOLD:
                    agents.append(agent)
        
        log(f"Discovered {len(agents)} agents from GitHub")
    
    except Exception as e:
        log(f"ERROR crawling GitHub: {e}")
    
    return agents

def deploy_agent(agent):
    """Deploy single agent to Railway database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if exists
        cur.execute(
            "SELECT id FROM agents WHERE source_url = %s",
            (agent["source_url"],)
        )
        
        if cur.fetchone():
            conn.close()
            return False  # Already exists
        
        # Insert new agent
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
        """, (
            agent_id,
            agent["name"][:255],
            agent.get("description", "AI agent")[:1000],
            agent["source_url"],
            "CAPABILITY",
            json.dumps({"tags": agent.get("capabilities", ["general_ai"])}),
            "UNVERIFIED",
            True,
            0.0,
            agent.get("evaluation_score", 50)
        ))
        
        conn.commit()
        conn.close()
        return True  # Successfully deployed
    
    except Exception as e:
        log(f"ERROR deploying {agent['name']}: {e}")
        return False

def main():
    """Main crawler execution"""
    log("="*60)
    log("CONTINUOUS CRAWLER - STARTING RUN")
    log("="*60)
    
    # Discover agents from multiple sources
    all_agents = []
    
    # HuggingFace (50 agents)
    all_agents.extend(crawl_huggingface_spaces(50))
    
    # GitHub (30 agents)
    all_agents.extend(crawl_github_ai(30))
    
    # Add more sources here as we expand
    # all_agents.extend(crawl_gpt_store(20))
    # all_agents.extend(crawl_poe(20))
    
    log(f"Total discovered: {len(all_agents)} agents")
    
    # Deploy to database
    deployed = 0
    skipped = 0
    failed = 0
    
    for agent in all_agents:
        result = deploy_agent(agent)
        if result is True:
            deployed += 1
        elif result is False:
            skipped += 1
        else:
            failed += 1
    
    log(f"RESULTS: Deployed={deployed} | Skipped={skipped} | Failed={failed}")
    log("="*60)
    
    return deployed

if __name__ == "__main__":
    try:
        deployed = main()
        sys.exit(0)
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        sys.exit(1)
