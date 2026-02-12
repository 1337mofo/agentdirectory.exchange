"""
Agent Discovery Crawler - PRODUCTION VERSION
Discovers AI agents from HuggingFace, GitHub, RapidAPI and auto-lists them
"""

import requests
import json
import time
from datetime import datetime
import os
from pathlib import Path

# Configuration
AGENT_DIRECTORY_API = "https://agentdirectory.exchange/api/v1"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Optional, increases rate limit
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")  # For creating agents

class AgentDiscoveryCrawler:
    def __init__(self):
        self.discovered_agents = []
        self.output_file = "discovered_agents.jsonl"
        
    def crawl_huggingface(self, limit=50):
        """Crawl HuggingFace for AI agent models"""
        print(f"[HUGGINGFACE] Searching for agents...")
        
        try:
            # Search for models tagged with 'agent' or 'autonomous'
            url = "https://huggingface.co/api/models"
            params = {
                "search": "agent",
                "limit": limit,
                "sort": "downloads",
                "direction": -1
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            models = response.json()
            
            for model in models:
                agent = {
                    "source": "huggingface",
                    "source_id": model.get("id"),
                    "name": self.clean_name(model.get("id", "")),
                    "description": model.get("description", "AI agent from HuggingFace"),
                    "source_url": f"https://huggingface.co/{model.get('id')}",
                    "metrics": {
                        "downloads": model.get("downloads", 0),
                        "likes": model.get("likes", 0)
                    },
                    "capabilities": ["general_ai"],
                    "discovered_at": datetime.utcnow().isoformat()
                }
                
                # Basic quality filter
                if agent["metrics"]["downloads"] > 100 or agent["metrics"]["likes"] > 5:
                    self.discovered_agents.append(agent)
            
            print(f"[HUGGINGFACE] Found {len([a for a in self.discovered_agents if a['source'] == 'huggingface'])} agents")
            return len(models)
            
        except Exception as e:
            print(f"[HUGGINGFACE] Error: {e}")
            return 0
    
    def crawl_github(self, limit=50):
        """Search GitHub for AI agent repositories"""
        print(f"[GITHUB] Searching for agent repositories...")
        
        try:
            headers = {}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
            
            url = "https://api.github.com/search/repositories"
            params = {
                "q": "ai-agent OR autonomous-agent language:Python",
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            repos = response.json().get("items", [])
            
            for repo in repos:
                agent = {
                    "source": "github",
                    "source_id": repo.get("full_name"),
                    "name": self.clean_name(repo.get("name", "")),
                    "description": repo.get("description", "AI agent from GitHub"),
                    "source_url": repo.get("html_url"),
                    "metrics": {
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "watchers": repo.get("watchers_count", 0)
                    },
                    "capabilities": ["general_ai"],
                    "discovered_at": datetime.utcnow().isoformat()
                }
                
                # Basic quality filter
                if agent["metrics"]["stars"] > 50:
                    self.discovered_agents.append(agent)
            
            print(f"[GITHUB] Found {len([a for a in self.discovered_agents if a['source'] == 'github'])} agents")
            return len(repos)
            
        except Exception as e:
            print(f"[GITHUB] Error: {e}")
            return 0
    
    def clean_name(self, raw_name):
        """Clean and format agent name"""
        if not raw_name:
            return "Unknown Agent"
        
        # Remove org prefix (e.g., "openai/gpt-4" -> "GPT-4")
        if "/" in raw_name:
            raw_name = raw_name.split("/")[-1]
        
        # Replace separators with spaces
        raw_name = raw_name.replace("-", " ").replace("_", " ")
        
        # Title case
        return raw_name.title()
    
    def evaluate_agent(self, agent):
        """Quick quality score for agent"""
        score = 0
        
        # Source quality
        if agent["source"] == "huggingface":
            score += min(agent["metrics"]["downloads"] / 1000, 30)
            score += min(agent["metrics"]["likes"] / 10, 20)
        elif agent["source"] == "github":
            score += min(agent["metrics"]["stars"] / 100, 30)
            score += min(agent["metrics"]["forks"] / 50, 20)
        
        # Description quality
        if agent.get("description") and len(agent["description"]) > 50:
            score += 20
        
        # Base quality
        score += 30
        
        return min(int(score), 100)
    
    def save_discoveries(self):
        """Save discovered agents to file"""
        with open(self.output_file, "a", encoding="utf-8") as f:
            for agent in self.discovered_agents:
                agent["evaluation_score"] = self.evaluate_agent(agent)
                f.write(json.dumps(agent) + "\n")
        
        print(f"[SAVE] Saved {len(self.discovered_agents)} agents to {self.output_file}")
    
    def upload_to_directory(self):
        """Upload agents to Agent Directory Exchange"""
        print(f"[UPLOAD] Uploading {len(self.discovered_agents)} agents to Agent Directory...")
        
        if not ADMIN_API_KEY:
            print("[UPLOAD] Warning: No ADMIN_API_KEY set. Skipping upload.")
            print("[UPLOAD] Set ADMIN_API_KEY environment variable to enable auto-upload.")
            return 0
        
        uploaded = 0
        for agent in self.discovered_agents:
            try:
                # Skip low-quality agents
                if agent.get("evaluation_score", 0) < 50:
                    continue
                
                # Create agent on platform
                agent_data = {
                    "name": agent["name"],
                    "description": agent["description"][:500],  # Truncate if too long
                    "source_url": agent["source_url"],
                    "capabilities": agent.get("capabilities", []),
                    "verified": False,  # Unverified until owner claims
                    "auto_discovered": True,
                    "discovery_source": agent["source"],
                    "discovery_score": agent.get("evaluation_score", 0)
                }
                
                response = requests.post(
                    f"{AGENT_DIRECTORY_API}/agents",
                    json=agent_data,
                    headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
                    timeout=30
                )
                
                if response.status_code == 201:
                    uploaded += 1
                    agent_id = response.json().get("agent", {}).get("id")
                    print(f"[UPLOAD] ✓ {agent['name']} (ID: {agent_id})")
                    
                    # Create default listing
                    self.create_listing(agent_id, agent)
                    time.sleep(1)  # Rate limiting
                    
                elif response.status_code == 409:
                    print(f"[UPLOAD] - {agent['name']} (already exists)")
                else:
                    print(f"[UPLOAD] ✗ {agent['name']} ({response.status_code})")
                
            except Exception as e:
                print(f"[UPLOAD] Error uploading {agent.get('name')}: {e}")
        
        print(f"[UPLOAD] Successfully uploaded {uploaded} new agents")
        return uploaded
    
    def create_listing(self, agent_id, agent):
        """Create default listing for agent"""
        try:
            listing_data = {
                "seller_agent_id": agent_id,
                "title": f"{agent['name']} - AI Agent Service",
                "description": agent["description"][:500],
                "listing_type": "capability",
                "category": "ai_services",
                "tags": agent.get("capabilities", []),
                "price_usd": 5.00,  # Default price
                "pricing_model": "per_use",
                "status": "active"
            }
            
            response = requests.post(
                f"{AGENT_DIRECTORY_API}/listings",
                json=listing_data,
                headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
                timeout=30
            )
            
            if response.status_code == 201:
                print(f"  └─ Listing created for {agent['name']}")
            
        except Exception as e:
            print(f"  └─ Listing failed: {e}")
    
    def run(self):
        """Run full discovery and upload pipeline"""
        print("=" * 60)
        print("AGENT DISCOVERY CRAWLER - STARTING")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Discover from all sources
        self.crawl_huggingface(limit=50)
        time.sleep(2)
        
        self.crawl_github(limit=50)
        time.sleep(2)
        
        print()
        print(f"[SUMMARY] Total discovered: {len(self.discovered_agents)}")
        
        # Save to file
        self.save_discoveries()
        
        # Upload to platform
        print()
        uploaded = self.upload_to_directory()
        
        print()
        print("=" * 60)
        print(f"CRAWLER COMPLETE - {uploaded} agents uploaded")
        print("=" * 60)
        
        return uploaded


if __name__ == "__main__":
    crawler = AgentDiscoveryCrawler()
    crawler.run()
