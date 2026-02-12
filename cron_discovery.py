"""
Cron Discovery Job - Runs on Railway Backend
Automatically discovers and deploys agents every hour
No manual intervention needed - fully automated
"""

import os
import sys
import json
import psycopg2
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# Aggressive settings
LIMIT_PER_SOURCE = 500
QUALITY_THRESHOLD = 40
MAX_WORKERS = 10

class AutomatedCrawler:
    """Runs automatically on Railway, no manual intervention"""
    
    def __init__(self):
        self.discovered = []
        self.deployed = 0
        
    def crawl_all_sources(self):
        """Parallel crawl all sources"""
        print(f"[CRON] Starting automated discovery...")
        
        crawlers = [
            self.crawl_huggingface_models,
            self.crawl_huggingface_spaces,
            self.crawl_github,
        ]
        
        all_agents = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(crawler) for crawler in crawlers]
            
            for future in as_completed(futures):
                try:
                    agents = future.result()
                    all_agents.extend(agents)
                except Exception as e:
                    print(f"[ERROR] Crawler failed: {e}")
        
        # Deduplicate
        seen = set()
        unique = []
        for agent in all_agents:
            url = agent.get("source_url")
            if url and url not in seen:
                seen.add(url)
                unique.append(agent)
        
        # Quality filter
        quality = []
        for agent in unique:
            agent["score"] = self.evaluate(agent)
            if agent["score"] >= QUALITY_THRESHOLD:
                quality.append(agent)
        
        self.discovered = quality
        print(f"[CRON] Discovered {len(quality)} high-quality agents")
        return quality
    
    def crawl_huggingface_models(self):
        """HuggingFace models"""
        try:
            url = "https://huggingface.co/api/models"
            params = {"search": "agent", "limit": LIMIT_PER_SOURCE, "sort": "downloads", "direction": -1}
            response = requests.get(url, params=params, timeout=30)
            models = response.json()
            
            agents = []
            for model in models:
                if model.get("downloads", 0) > 50:
                    agents.append({
                        "source": "huggingface_models",
                        "source_id": model.get("id"),
                        "name": self.clean_name(model.get("id", "")),
                        "description": (model.get("description") or "AI model")[:500],
                        "source_url": f"https://huggingface.co/{model.get('id')}",
                        "metrics": {"downloads": model.get("downloads", 0), "likes": model.get("likes", 0)}
                    })
            return agents
        except Exception as e:
            print(f"[HF-MODELS] Error: {e}")
            return []
    
    def crawl_huggingface_spaces(self):
        """HuggingFace spaces"""
        try:
            url = "https://huggingface.co/api/spaces"
            params = {"limit": LIMIT_PER_SOURCE, "sort": "likes", "direction": -1}
            response = requests.get(url, params=params, timeout=30)
            spaces = response.json()
            
            agents = []
            for space in spaces:
                if space.get("likes", 0) > 2:
                    agents.append({
                        "source": "huggingface_spaces",
                        "source_id": space.get("id"),
                        "name": self.clean_name(space.get("id", "")),
                        "description": "AI application"[:500],
                        "source_url": f"https://huggingface.co/spaces/{space.get('id')}",
                        "metrics": {"likes": space.get("likes", 0)}
                    })
            return agents
        except Exception as e:
            print(f"[HF-SPACES] Error: {e}")
            return []
    
    def crawl_github(self):
        """GitHub repos"""
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
            url = "https://api.github.com/search/repositories"
            params = {"q": "ai-agent language:Python", "sort": "stars", "order": "desc", "per_page": LIMIT_PER_SOURCE}
            response = requests.get(url, params=params, headers=headers, timeout=30)
            repos = response.json().get("items", [])
            
            agents = []
            for repo in repos:
                if repo.get("stargazers_count", 0) > 20:
                    agents.append({
                        "source": "github",
                        "source_id": repo.get("full_name"),
                        "name": self.clean_name(repo.get("name", "")),
                        "description": (repo.get("description") or "AI agent")[:500],
                        "source_url": repo.get("html_url"),
                        "metrics": {"stars": repo.get("stargazers_count", 0)}
                    })
            return agents
        except Exception as e:
            print(f"[GITHUB] Error: {e}")
            return []
    
    def clean_name(self, name):
        """Clean name"""
        if not name:
            return "Agent"
        if "/" in name:
            name = name.split("/")[-1]
        return name.replace("-", " ").replace("_", " ").title()[:255]
    
    def evaluate(self, agent):
        """Score agent"""
        score = 30
        if agent["source"] == "huggingface_models":
            score += min(agent["metrics"].get("downloads", 0) / 500, 50)
        elif agent["source"] == "huggingface_spaces":
            score += min(agent["metrics"].get("likes", 0) / 3, 50)
        elif agent["source"] == "github":
            score += min(agent["metrics"].get("stars", 0) / 50, 50)
        if agent.get("description") and len(agent["description"]) > 50:
            score += 20
        return min(int(score), 100)
    
    def deploy_to_database(self):
        """Deploy directly to database"""
        if not DATABASE_URL:
            print("[ERROR] DATABASE_URL not set")
            return 0
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            print(f"[CRON] Connected to database")
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return 0
        
        deployed = 0
        for agent in self.discovered:
            try:
                # Check if exists
                cur.execute("SELECT id FROM agents WHERE source_url = %s", (agent["source_url"],))
                if cur.fetchone():
                    continue
                
                # Insert agent
                cur.execute("""
                    INSERT INTO agents (
                        name, description, source_url, agent_type,
                        capabilities, verified, is_active, rating_avg,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, 'general', ARRAY['general_ai'],
                        false, true, 0.0, NOW(), NOW()
                    ) RETURNING id
                """, (agent["name"], agent["description"], agent["source_url"]))
                
                agent_id = cur.fetchone()[0]
                
                # Create listing
                cur.execute("""
                    INSERT INTO listings (
                        seller_agent_id, title, description, listing_type,
                        category, price_usd, pricing_model, status,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, 'capability', 'ai_services',
                        5.00, 'per_use', 'active', NOW(), NOW()
                    )
                """, (agent_id, f"{agent['name']} - AI Agent Service", agent["description"]))
                
                deployed += 1
                
                if deployed % 50 == 0:
                    conn.commit()
                    print(f"[CRON] Deployed {deployed} agents...")
            
            except Exception as e:
                print(f"[ERROR] Failed to deploy {agent.get('name')}: {e}")
                conn.rollback()
        
        conn.commit()
        cur.close()
        conn.close()
        
        self.deployed = deployed
        print(f"[CRON] Deployment complete: {deployed} new agents")
        return deployed
    
    def run(self):
        """Main cron job"""
        print("=" * 60)
        print("AUTOMATED DISCOVERY - CRON JOB")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Discover
        agents = self.crawl_all_sources()
        
        # Deploy
        deployed = self.deploy_to_database()
        
        print("=" * 60)
        print(f"CRON COMPLETE - {deployed} new agents deployed")
        print("=" * 60)
        
        return deployed


if __name__ == "__main__":
    crawler = AutomatedCrawler()
    count = crawler.run()
    sys.exit(0 if count >= 0 else 1)
