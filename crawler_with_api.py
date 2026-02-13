"""
Agent Discovery Crawler with Automated Upload
Uses Admin API Key to submit discovered agents directly to database

This is Option B - automated crawler with API authentication
"""
import requests
import json
from datetime import datetime
import time
import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://agentdirectory.exchange")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", None)

if not ADMIN_API_KEY:
    print("ERROR: ADMIN_API_KEY environment variable not set")
    print("Set it with: set ADMIN_API_KEY=your_key_here")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {ADMIN_API_KEY}",
    "Content-Type": "application/json"
}

# Quality scoring thresholds
MIN_QUALITY_SCORE = 50  # Agents below this are not submitted
AUTO_APPROVE_SCORE = 70  # Agents above this are auto-approved


def discover_huggingface_agents(limit=100):
    """
    Discover AI agents on HuggingFace
    Returns list of agent data dictionaries
    """
    print(f"[HUGGINGFACE] Searching for agents (limit: {limit})...")
    
    discovered = []
    
    try:
        # Search HuggingFace for agent models
        search_url = "https://huggingface.co/api/models"
        params = {
            "search": "agent",
            "limit": limit,
            "sort": "downloads",
            "direction": -1
        }
        
        response = requests.get(search_url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"[HUGGINGFACE] API error: {response.status_code}")
            return discovered
        
        models = response.json()
        
        for model in models:
            model_id = model.get("id", "")
            
            # Basic quality evaluation
            downloads = model.get("downloads", 0)
            likes = model.get("likes", 0)
            
            # Quality score based on popularity
            quality_score = min(100, 50 + (downloads // 100) + (likes * 5))
            
            agent_data = {
                "name": model_id.split("/")[-1],
                "description": model.get("tags", [])[:5] if model.get("tags") else "HuggingFace AI model",
                "source_url": f"https://huggingface.co/{model_id}",
                "discovery_source": "huggingface",
                "quality_score": quality_score,
                "agent_type": "AI Model",
                "categories": model.get("tags", [])[:3]
            }
            
            # Convert description list to string if needed
            if isinstance(agent_data["description"], list):
                agent_data["description"] = ", ".join(agent_data["description"])
            
            # Ensure description is at least 10 chars
            if len(agent_data["description"]) < 10:
                agent_data["description"] = f"AI agent model from HuggingFace: {agent_data['name']}"
            
            discovered.append(agent_data)
        
        print(f"[HUGGINGFACE] Found {len(discovered)} agents")
        
    except Exception as e:
        print(f"[HUGGINGFACE] Error: {e}")
    
    return discovered


def discover_github_agents(limit=50):
    """
    Discover AI agent repositories on GitHub
    Returns list of agent data dictionaries
    """
    print(f"[GITHUB] Searching for agent repositories (limit: {limit})...")
    
    discovered = []
    
    try:
        # Search GitHub for agent repositories
        search_url = "https://api.github.com/search/repositories"
        params = {
            "q": "ai agent OR autonomous agent",
            "sort": "stars",
            "per_page": limit
        }
        
        response = requests.get(search_url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"[GITHUB] API error: {response.status_code}")
            return discovered
        
        repos = response.json().get("items", [])
        
        for repo in repos:
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            
            # Quality score based on GitHub metrics
            quality_score = min(100, 50 + (stars // 10) + (forks // 5))
            
            agent_data = {
                "name": repo.get("name", "Unknown"),
                "description": repo.get("description", "GitHub AI agent repository")[:500],
                "source_url": repo.get("html_url", ""),
                "discovery_source": "github",
                "quality_score": quality_score,
                "agent_type": "Open Source Agent",
                "categories": repo.get("topics", [])[:3]
            }
            
            # Ensure description is at least 10 chars
            if len(agent_data["description"]) < 10:
                agent_data["description"] = f"Open source AI agent repository: {agent_data['name']}"
            
            discovered.append(agent_data)
        
        print(f"[GITHUB] Found {len(discovered)} agents")
        
    except Exception as e:
        print(f"[GITHUB] Error: {e}")
    
    return discovered


def submit_agents_to_api(agents, dry_run=False):
    """
    Submit discovered agents to Agent Directory via API
    
    Args:
        agents: List of agent dictionaries
        dry_run: If True, validate but don't actually submit
    
    Returns:
        API response dictionary
    """
    if not agents:
        print("[SUBMIT] No agents to submit")
        return None
    
    # Filter by quality score
    filtered_agents = [a for a in agents if a["quality_score"] >= MIN_QUALITY_SCORE]
    
    print(f"[SUBMIT] Filtered {len(agents)} → {len(filtered_agents)} agents (quality >= {MIN_QUALITY_SCORE})")
    
    if not filtered_agents:
        print("[SUBMIT] No agents passed quality filter")
        return None
    
    # Prepare batch submission
    payload = {
        "agents": filtered_agents,
        "crawler_run_id": f"run_{int(time.time())}",
        "dry_run": dry_run
    }
    
    # Submit to API
    endpoint = f"{API_BASE_URL}/api/v1/crawler/submit"
    
    print(f"[SUBMIT] Submitting {len(filtered_agents)} agents to {endpoint}")
    if dry_run:
        print("[SUBMIT] DRY RUN MODE - No agents will be created")
    
    try:
        response = requests.post(endpoint, json=payload, headers=HEADERS, timeout=60)
        
        if response.status_code == 201:
            result = response.json()
            print(f"[SUBMIT] ✓ Success!")
            print(f"[SUBMIT]   Created: {result['agents_created']}")
            print(f"[SUBMIT]   Skipped: {result['agents_skipped']}")
            
            if result.get('skipped_reasons'):
                print(f"[SUBMIT] Skipped reasons:")
                for name, reason in list(result['skipped_reasons'].items())[:5]:
                    print(f"[SUBMIT]   - {name}: {reason}")
            
            return result
        else:
            print(f"[SUBMIT] ✗ API Error: {response.status_code}")
            print(f"[SUBMIT] Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"[SUBMIT] ✗ Error: {e}")
        return None


def get_crawler_stats():
    """Get statistics about auto-discovered agents"""
    endpoint = f"{API_BASE_URL}/api/v1/crawler/stats"
    
    try:
        response = requests.get(endpoint, headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            stats = response.json()
            print("\n[STATS] Crawler Statistics:")
            print(f"  Total Discovered: {stats['total_discovered']}")
            print(f"  Auto-Approved: {stats['auto_approved']}")
            print(f"  Pending Review: {stats['pending_review']}")
            print(f"  Average Quality: {stats['average_quality_score']}")
            
            if stats.get('by_source'):
                print(f"  By Source:")
                for source, count in stats['by_source'].items():
                    print(f"    - {source}: {count}")
            
            return stats
        else:
            print(f"[STATS] Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[STATS] Error: {e}")
        return None


def main():
    """
    Main crawler execution
    """
    print("\n🦅 Agent Directory Crawler with API Upload")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base: {API_BASE_URL}")
    print(f"API Key: {ADMIN_API_KEY[:20]}...")
    print("=" * 60 + "\n")
    
    # Discover agents from multiple sources
    all_agents = []
    
    # HuggingFace
    hf_agents = discover_huggingface_agents(limit=100)
    all_agents.extend(hf_agents)
    
    # GitHub
    gh_agents = discover_github_agents(limit=50)
    all_agents.extend(gh_agents)
    
    print(f"\n[SUMMARY] Total discovered: {len(all_agents)} agents")
    
    # Submit to API
    if all_agents:
        result = submit_agents_to_api(all_agents, dry_run=False)
        
        if result and result['success']:
            print(f"\n✅ Crawler completed successfully")
            print(f"   {result['agents_created']} agents added to directory")
        else:
            print(f"\n⚠️  Crawler completed with errors")
    else:
        print("\n⚠️  No agents discovered")
    
    # Get updated stats
    print("\n" + "=" * 60)
    get_crawler_stats()
    print("=" * 60)
    
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
