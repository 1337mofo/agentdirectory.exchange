"""
Agent Discovery Crawler V2 - AGGRESSIVE MODE
Goal: 10,000+ agents in 7 days
Strategy: 10 sources, 500/source, hourly runs, parallel execution
"""

import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Configuration
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# Aggressive settings
LIMIT_PER_SOURCE = 500  # 10× increase from v1
QUALITY_THRESHOLD = 40  # Lowered from 50
MAX_WORKERS = 10  # Parallel execution

class AggressiveCrawler:
    def __init__(self):
        self.discovered = []
        self.stats = {
            "total": 0,
            "by_source": {},
            "high_quality": 0,
            "duplicates": 0
        }
    
    def crawl_huggingface_models(self):
        """HuggingFace Models - 50K+ potential"""
        print(f"[HF-MODELS] Crawling...")
        try:
            agents = []
            url = "https://huggingface.co/api/models"
            params = {"search": "agent", "limit": LIMIT_PER_SOURCE, "sort": "downloads", "direction": -1}
            
            response = requests.get(url, params=params, timeout=30)
            models = response.json()
            
            for model in models:
                if model.get("downloads", 0) > 50:  # Lowered threshold
                    agents.append({
                        "source": "huggingface_models",
                        "source_id": model.get("id"),
                        "name": self.clean_name(model.get("id", "")),
                        "description": model.get("description", "AI model from HuggingFace")[:500],
                        "source_url": f"https://huggingface.co/{model.get('id')}",
                        "metrics": {"downloads": model.get("downloads", 0), "likes": model.get("likes", 0)},
                        "capabilities": ["ml_model"],
                        "discovered_at": datetime.utcnow().isoformat()
                    })
            
            self.stats["by_source"]["huggingface_models"] = len(agents)
            return agents
        except Exception as e:
            print(f"[HF-MODELS] Error: {e}")
            return []
    
    def crawl_huggingface_spaces(self):
        """HuggingFace Spaces - 50K+ potential"""
        print(f"[HF-SPACES] Crawling...")
        try:
            agents = []
            url = "https://huggingface.co/api/spaces"
            params = {"limit": LIMIT_PER_SOURCE, "sort": "likes", "direction": -1}
            
            response = requests.get(url, params=params, timeout=30)
            spaces = response.json()
            
            for space in spaces:
                if space.get("likes", 0) > 2:  # Lowered threshold
                    agents.append({
                        "source": "huggingface_spaces",
                        "source_id": space.get("id"),
                        "name": self.clean_name(space.get("id", "")),
                        "description": "AI application from HuggingFace Spaces"[:500],
                        "source_url": f"https://huggingface.co/spaces/{space.get('id')}",
                        "metrics": {"likes": space.get("likes", 0)},
                        "capabilities": ["ai_application"],
                        "discovered_at": datetime.utcnow().isoformat()
                    })
            
            self.stats["by_source"]["huggingface_spaces"] = len(agents)
            return agents
        except Exception as e:
            print(f"[HF-SPACES] Error: {e}")
            return []
    
    def crawl_github(self):
        """GitHub - 100K+ potential"""
        print(f"[GITHUB] Crawling...")
        try:
            agents = []
            headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
            
            queries = [
                "ai-agent language:Python",
                "autonomous-agent language:Python",
                "llm-agent language:Python"
            ]
            
            for query in queries:
                url = "https://api.github.com/search/repositories"
                params = {"q": query, "sort": "stars", "order": "desc", "per_page": LIMIT_PER_SOURCE // len(queries)}
                
                response = requests.get(url, params=params, headers=headers, timeout=30)
                repos = response.json().get("items", [])
                
                for repo in repos:
                    if repo.get("stargazers_count", 0) > 20:  # Lowered threshold
                        agents.append({
                            "source": "github",
                            "source_id": repo.get("full_name"),
                            "name": self.clean_name(repo.get("name", "")),
                            "description": (repo.get("description") or "AI agent from GitHub")[:500],
                            "source_url": repo.get("html_url"),
                            "metrics": {"stars": repo.get("stargazers_count", 0), "forks": repo.get("forks_count", 0)},
                            "capabilities": ["code_repository"],
                            "discovered_at": datetime.utcnow().isoformat()
                        })
            
            self.stats["by_source"]["github"] = len(agents)
            return agents
        except Exception as e:
            print(f"[GITHUB] Error: {e}")
            return []
    
    def crawl_replicate(self):
        """Replicate - 10K+ potential"""
        print(f"[REPLICATE] Crawling...")
        try:
            agents = []
            url = "https://replicate.com/api/models"
            params = {"limit": LIMIT_PER_SOURCE}
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                models = response.json().get("results", [])
                
                for model in models:
                    agents.append({
                        "source": "replicate",
                        "source_id": f"{model.get('owner')}/{model.get('name')}",
                        "name": self.clean_name(model.get("name", "")),
                        "description": (model.get("description") or "AI model from Replicate")[:500],
                        "source_url": f"https://replicate.com/{model.get('owner')}/{model.get('name')}",
                        "metrics": {"runs": model.get("run_count", 0)},
                        "capabilities": ["ml_model"],
                        "discovered_at": datetime.utcnow().isoformat()
                    })
            
            self.stats["by_source"]["replicate"] = len(agents)
            return agents
        except Exception as e:
            print(f"[REPLICATE] Error: {e}")
            return []
    
    def crawl_rapidapi(self):
        """RapidAPI - 5K+ AI APIs"""
        print(f"[RAPIDAPI] Crawling...")
        try:
            agents = []
            if not RAPIDAPI_KEY:
                print(f"[RAPIDAPI] Skipped (no API key)")
                return []
            
            # Search for AI-related APIs
            url = "https://rapidapi.com/search/ai"
            # Note: RapidAPI doesn't have a public API for browsing, would need scraping
            # Placeholder for now
            
            self.stats["by_source"]["rapidapi"] = len(agents)
            return agents
        except Exception as e:
            print(f"[RAPIDAPI] Error: {e}")
            return []
    
    def clean_name(self, raw_name):
        """Clean and format name"""
        if not raw_name:
            return "Unknown Agent"
        if "/" in raw_name:
            raw_name = raw_name.split("/")[-1]
        return raw_name.replace("-", " ").replace("_", " ").title()[:255]
    
    def evaluate(self, agent):
        """Quick quality score (lowered threshold)"""
        score = 30  # Base score
        
        if agent["source"] == "huggingface_models":
            score += min(agent["metrics"].get("downloads", 0) / 500, 30)
            score += min(agent["metrics"].get("likes", 0) / 5, 20)
        elif agent["source"] == "huggingface_spaces":
            score += min(agent["metrics"].get("likes", 0) / 3, 50)
        elif agent["source"] == "github":
            score += min(agent["metrics"].get("stars", 0) / 50, 30)
            score += min(agent["metrics"].get("forks", 0) / 25, 20)
        elif agent["source"] == "replicate":
            score += min(agent["metrics"].get("runs", 0) / 100, 50)
        
        if agent.get("description") and len(agent["description"]) > 50:
            score += 20
        
        return min(int(score), 100)
    
    def run_parallel(self):
        """Run all crawlers in parallel"""
        print("=" * 60)
        print("AGGRESSIVE CRAWLER V2 - STARTING")
        print("=" * 60)
        print(f"Target: {LIMIT_PER_SOURCE} per source")
        print(f"Quality threshold: {QUALITY_THRESHOLD}/100")
        print(f"Parallel workers: {MAX_WORKERS}")
        print()
        
        crawlers = [
            self.crawl_huggingface_models,
            self.crawl_huggingface_spaces,
            self.crawl_github,
            self.crawl_replicate,
            # self.crawl_rapidapi,  # Add when API key available
        ]
        
        all_agents = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_crawler = {executor.submit(crawler): crawler.__name__ for crawler in crawlers}
            
            for future in as_completed(future_to_crawler):
                crawler_name = future_to_crawler[future]
                try:
                    agents = future.result()
                    all_agents.extend(agents)
                    print(f"[DONE] {crawler_name}: {len(agents)} agents")
                except Exception as e:
                    print(f"[ERROR] {crawler_name}: {e}")
        
        print()
        print(f"[TOTAL] Discovered: {len(all_agents)} agents")
        
        # Deduplicate by source_url
        seen = set()
        unique_agents = []
        for agent in all_agents:
            url = agent.get("source_url")
            if url and url not in seen:
                seen.add(url)
                unique_agents.append(agent)
            else:
                self.stats["duplicates"] += 1
        
        print(f"[UNIQUE] After dedup: {len(unique_agents)} agents")
        print(f"[DUPLICATES] Removed: {self.stats['duplicates']}")
        
        # Evaluate and filter
        quality_agents = []
        for agent in unique_agents:
            agent["evaluation_score"] = self.evaluate(agent)
            if agent["evaluation_score"] >= QUALITY_THRESHOLD:
                quality_agents.append(agent)
                self.stats["high_quality"] += 1
        
        print(f"[QUALITY] Above {QUALITY_THRESHOLD}: {len(quality_agents)} agents")
        print()
        
        # Save
        self.discovered = quality_agents
        self.save_to_file()
        
        print("=" * 60)
        print(f"DISCOVERY COMPLETE - {len(quality_agents)} agents ready")
        print("=" * 60)
        print()
        print("Next: Run deploy_crawler_production.py to upload")
        
        return len(quality_agents)
    
    def save_to_file(self):
        """Save discovered agents"""
        with open("discovered_agents_v2.jsonl", "w", encoding="utf-8") as f:
            for agent in self.discovered:
                f.write(json.dumps(agent) + "\n")
        print(f"[SAVE] Saved to discovered_agents_v2.jsonl")


if __name__ == "__main__":
    crawler = AggressiveCrawler()
    count = crawler.run_parallel()
    
    print(f"\n[STATS] Total discovered: {count}")
    print(f"[STATS] By source:")
    for source, num in crawler.stats["by_source"].items():
        print(f"  - {source}: {num}")
