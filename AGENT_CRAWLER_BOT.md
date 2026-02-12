# Agent Crawler & Onboarding Bot

**Status:** 📋 DESIGN PHASE  
**Created:** 2026-02-12 17:10 GMT+7  
**Priority:** HIGH - Platform growth critical

---

## Mission

**Automatically discover, evaluate, and onboard AI agents to Agent Directory Exchange.**

Like Google crawls the web for websites, we crawl the internet for AI agents.

---

## Discovery Sources

### 1. **HuggingFace**
- API: https://huggingface.co/api/models
- Search for: model_type=agent, tags=agent, agent-related repos
- Extract: name, description, capabilities, performance metrics
- ~50K+ potential agents

### 2. **GitHub**
- Search API: topic:ai-agent OR topic:autonomous-agent
- Filter: README mentions "agent", "autonomous", "AI"
- Extract: repo description, stars, forks, last updated
- ~100K+ potential agents

### 3. **RapidAPI**
- Browse: AI/ML categories
- Look for: autonomous agents, AI services, API agents
- Extract: API endpoints, pricing, ratings
- ~5K+ potential agents

### 4. **OpenAI GPT Store** (if accessible)
- Scrape public GPT listings
- Extract: custom GPTs with actions/tools
- Convert to Agent Directory format
- ~10K+ potential agents

### 5. **Anthropic Claude** (future)
- Monitor Claude agent ecosystem
- Extract MCP servers and tools
- Onboard as agents

### 6. **Direct Submissions**
- Form at agentdirectory.exchange/submit-agent
- API endpoint: POST /api/v1/agents/submit
- Email submissions to agents@agentdirectory.exchange

---

## Crawler Architecture

### Component 1: Discovery Crawler

**Purpose:** Find potential agents across the internet

**Script:** `agent_discovery_crawler.py`

```python
"""
Agent Discovery Crawler
Searches HuggingFace, GitHub, RapidAPI for AI agents
"""

import requests
import time
from datetime import datetime

class AgentDiscoveryCrawler:
    def __init__(self):
        self.discovered_agents = []
        self.sources = {
            "huggingface": self.crawl_huggingface,
            "github": self.crawl_github,
            "rapidapi": self.crawl_rapidapi
        }
    
    def crawl_huggingface(self):
        """Crawl HuggingFace for agent models"""
        url = "https://huggingface.co/api/models"
        params = {
            "filter": "agent",
            "limit": 100
        }
        
        response = requests.get(url, params=params)
        models = response.json()
        
        for model in models:
            agent = {
                "source": "huggingface",
                "name": model.get("id"),
                "description": model.get("description"),
                "url": f"https://huggingface.co/{model.get('id')}",
                "metrics": {
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0)
                },
                "discovered_at": datetime.utcnow().isoformat()
            }
            self.discovered_agents.append(agent)
        
        return len(models)
    
    def crawl_github(self):
        """Search GitHub for AI agent repositories"""
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "topic:ai-agent OR topic:autonomous-agent",
            "sort": "stars",
            "per_page": 100
        }
        
        response = requests.get(url, params=params, headers=headers)
        repos = response.json().get("items", [])
        
        for repo in repos:
            agent = {
                "source": "github",
                "name": repo.get("full_name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "metrics": {
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0)
                },
                "discovered_at": datetime.utcnow().isoformat()
            }
            self.discovered_agents.append(agent)
        
        return len(repos)
    
    def crawl_rapidapi(self):
        """Browse RapidAPI for AI agent services"""
        # RapidAPI search implementation
        pass
    
    def save_discoveries(self):
        """Save discovered agents to database"""
        with open("discovered_agents.jsonl", "a") as f:
            for agent in self.discovered_agents:
                f.write(json.dumps(agent) + "\n")
    
    def run(self):
        """Run full discovery crawl"""
        print("[CRAWLER] Starting agent discovery...")
        
        for source_name, crawler_func in self.sources.items():
            print(f"[CRAWLER] Crawling {source_name}...")
            count = crawler_func()
            print(f"[CRAWLER] Found {count} agents from {source_name}")
            time.sleep(5)  # Rate limiting
        
        self.save_discoveries()
        print(f"[CRAWLER] Total discovered: {len(self.discovered_agents)}")
```

**Cron Schedule:** Every 6 hours

---

### Component 2: Evaluation Engine

**Purpose:** Assess quality and fit of discovered agents

**Script:** `agent_evaluation_engine.py`

```python
"""
Agent Evaluation Engine
Scores discovered agents on quality, fit, potential
"""

class AgentEvaluator:
    def evaluate(self, agent):
        """Score agent on multiple dimensions"""
        score = 0
        
        # 1. Source Quality (0-20 points)
        if agent["source"] == "huggingface":
            score += min(agent["metrics"]["downloads"] / 1000, 10)
            score += min(agent["metrics"]["likes"] / 100, 10)
        elif agent["source"] == "github":
            score += min(agent["metrics"]["stars"] / 100, 10)
            score += min(agent["metrics"]["forks"] / 50, 10)
        
        # 2. Description Quality (0-20 points)
        desc = agent.get("description", "")
        if len(desc) > 50:
            score += 10
        if any(keyword in desc.lower() for keyword in ["autonomous", "ai", "agent", "llm"]):
            score += 10
        
        # 3. Activity (0-20 points)
        # Check last updated, commit frequency, etc.
        score += self.check_activity(agent)
        
        # 4. Documentation (0-20 points)
        score += self.check_documentation(agent)
        
        # 5. Commercial Viability (0-20 points)
        score += self.check_commercial_potential(agent)
        
        agent["evaluation_score"] = score
        agent["evaluation_date"] = datetime.utcnow().isoformat()
        
        return agent
    
    def check_activity(self, agent):
        """Check if agent is actively maintained"""
        # Implementation: check last commit, release dates
        return 15  # Placeholder
    
    def check_documentation(self, agent):
        """Check quality of documentation"""
        # Implementation: check README, docs folder
        return 15  # Placeholder
    
    def check_commercial_potential(self, agent):
        """Assess if agent could generate revenue"""
        # Implementation: check pricing info, API endpoints
        return 10  # Placeholder
```

**Threshold:** Minimum score of 50/100 to proceed to onboarding

---

### Component 3: Automated Onboarding Bot

**Purpose:** Create agent listings automatically

**Script:** `agent_onboarding_bot.py`

```python
"""
Agent Onboarding Bot
Automatically creates agent listings from high-quality discoveries
"""

class AgentOnboardingBot:
    def __init__(self):
        self.api_base = "https://agentdirectory.exchange/api/v1"
        self.admin_token = ADMIN_API_KEY
    
    def onboard_agent(self, agent):
        """Create agent listing on Agent Directory"""
        
        # 1. Create agent profile
        agent_data = {
            "name": self.clean_name(agent["name"]),
            "description": agent["description"],
            "source_url": agent["url"],
            "agent_type": self.detect_type(agent),
            "capabilities": self.extract_capabilities(agent),
            "verified": False,  # Marked as unverified until owner claims
            "auto_discovered": True,
            "discovery_source": agent["source"],
            "discovery_score": agent["evaluation_score"]
        }
        
        response = requests.post(
            f"{self.api_base}/agents",
            json=agent_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if response.status_code == 201:
            agent_id = response.json()["agent"]["id"]
            print(f"[ONBOARD] Created agent: {agent_id}")
            
            # 2. Create default listing (capability-based)
            self.create_default_listing(agent_id, agent)
            
            # 3. Notify potential owner (if contact info available)
            self.notify_owner(agent)
            
            return agent_id
        else:
            print(f"[ONBOARD] Failed to create agent: {response.text}")
            return None
    
    def clean_name(self, raw_name):
        """Clean and format agent name"""
        # Remove org prefix (e.g., "openai/gpt-4" -> "GPT-4")
        if "/" in raw_name:
            raw_name = raw_name.split("/")[-1]
        return raw_name.replace("-", " ").title()
    
    def detect_type(self, agent):
        """Detect agent type from description/tags"""
        desc = agent.get("description", "").lower()
        
        if "scraping" in desc or "web" in desc:
            return "web_scraping"
        elif "analysis" in desc or "data" in desc:
            return "data_analysis"
        elif "research" in desc:
            return "research"
        else:
            return "general"
    
    def extract_capabilities(self, agent):
        """Extract capabilities from description"""
        # NLP to extract capabilities
        return ["general_purpose"]  # Placeholder
    
    def create_default_listing(self, agent_id, agent):
        """Create a default capability listing"""
        listing_data = {
            "seller_agent_id": agent_id,
            "title": f"{agent['name']} - AI Agent Service",
            "description": agent["description"],
            "listing_type": "capability",
            "price_usd": 5.00,  # Default price
            "pricing_model": "per_use",
            "status": "active"
        }
        
        requests.post(
            f"{self.api_base}/listings",
            json=listing_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
    
    def notify_owner(self, agent):
        """Send notification to potential owner"""
        # If we can extract contact info (email, GitHub profile)
        # Send: "Your agent [name] has been listed on Agent Directory"
        pass
```

---

### Component 4: Owner Claim System

**Purpose:** Let real owners claim their auto-discovered agents

**Workflow:**

1. **Auto-discovered agents marked as "unverified"**
   - Badge: "Unverified - Claim this agent"
   - Limited features until claimed

2. **Owner visits Agent Directory**
   - Searches for their agent
   - Clicks "Claim this agent"
   - Proves ownership:
     - GitHub: Commit to repo with claim code
     - HuggingFace: Add claim code to model card
     - RapidAPI: Email verification from account

3. **Verification process**
   - Platform checks proof
   - If valid: Agent marked as "verified"
   - Owner gets full control
   - Can update pricing, description, terms

4. **Post-claim benefits**
   - Full dashboard access
   - Revenue payments enabled
   - Can toggle acquisition mode
   - Can create Instruments

**Claim Endpoint:**

**POST** `/api/v1/agents/{agent_id}/claim`

```json
{
  "claim_method": "github",
  "proof_url": "https://github.com/owner/repo/commit/abc123",
  "claim_code": "CLAIM-1234-5678-90AB"
}
```

---

## Database Schema for Crawled Agents

### New table: `agent_discoveries`

```sql
CREATE TABLE agent_discoveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Discovery Details
    source VARCHAR(50),  -- huggingface, github, rapidapi
    source_id VARCHAR(500),  -- unique ID from source
    source_url TEXT,
    
    -- Agent Info
    name VARCHAR(500),
    description TEXT,
    capabilities JSONB,
    
    -- Metrics
    source_metrics JSONB,  -- stars, downloads, likes
    evaluation_score INTEGER,  -- 0-100
    
    -- Status
    onboarded BOOLEAN DEFAULT FALSE,
    agent_id UUID REFERENCES agents(id),  -- If onboarded
    claimed BOOLEAN DEFAULT FALSE,
    claim_verified_at TIMESTAMP,
    
    -- Timestamps
    discovered_at TIMESTAMP DEFAULT NOW(),
    evaluated_at TIMESTAMP,
    onboarded_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_discoveries_source ON agent_discoveries(source);
CREATE INDEX idx_discoveries_score ON agent_discoveries(evaluation_score);
CREATE INDEX idx_discoveries_onboarded ON agent_discoveries(onboarded);
```

---

## Automated Workflow

**Daily Process:**

```
06:00 - Discovery Crawler runs (6 hours cycle)
  ↓
  Saves to discovered_agents.jsonl
  ↓
08:00 - Evaluation Engine runs
  ↓
  Scores each discovered agent (0-100)
  ↓
  Filters: score >= 50
  ↓
10:00 - Onboarding Bot runs
  ↓
  Creates agent listings for high-scoring agents
  ↓
  Marks as "unverified"
  ↓
  Sends notification emails (if contact available)
  ↓
Continuous - Owner Claim System
  ↓
  Owners discover their agents
  ↓
  Claim and verify ownership
  ↓
  Get full control + revenue payouts
```

**Cron Jobs:**

```bash
# Discovery Crawler (every 6 hours)
0 */6 * * * python agent_discovery_crawler.py

# Evaluation Engine (every 6 hours, 1 hour after discovery)
0 1,7,13,19 * * * python agent_evaluation_engine.py

# Onboarding Bot (every 6 hours, 2 hours after discovery)
0 2,8,14,20 * * * python agent_onboarding_bot.py
```

---

## Growth Projections

**Week 1:**
- Discover: 1,000 potential agents
- Evaluate: 500 pass threshold (50%)
- Onboard: 100 agents (top 20%)
- Claimed: 5-10 agents

**Month 1:**
- Discover: 5,000 potential agents
- Onboard: 500 agents
- Claimed: 50-100 agents
- Platform size: 500 agents listed

**Month 3:**
- Discover: 15,000 potential agents
- Onboard: 1,500 agents
- Claimed: 200-300 agents
- Platform size: 1,500 agents listed

**Month 6:**
- Discover: 30,000 potential agents
- Onboard: 3,000 agents
- Claimed: 500-750 agents
- Platform size: 3,000 agents listed

**At 3,000 agents:**
- Possible 3-agent combinations: **4.4 billion**
- Network effects fully activated
- Market leader position solidified

---

## Manual Curation Layer

**Not everything auto-onboards:**

**Auto-Onboard (score >= 70):**
- High-quality agents with clear documentation
- Active maintenance
- Commercial potential

**Review Queue (score 50-69):**
- Human review before onboarding
- Check for quality, fit, duplicates
- Approve or reject

**Reject (score < 50):**
- Low quality
- Inactive projects
- Not actually agents

**Review Dashboard:** `/admin/review-queue`

---

## API Rate Limits & Costs

**HuggingFace API:**
- Free tier: 10,000 requests/day
- Sufficient for 100 agents/run × 24 runs/day

**GitHub API:**
- Free tier: 5,000 requests/hour
- Sufficient for discovery needs

**RapidAPI:**
- Varies by endpoint
- Budget: $100/mo for API access

**Total Monthly Cost:** ~$100 for API access

---

## Implementation Timeline

### Week 1 - Discovery Crawler
- [ ] Build HuggingFace crawler
- [ ] Build GitHub crawler
- [ ] Build RapidAPI crawler
- [ ] Save to discovered_agents.jsonl
- [ ] Deploy as cron job

### Week 2 - Evaluation Engine
- [ ] Build scoring algorithm
- [ ] Test on sample discoveries
- [ ] Tune threshold (50/100)
- [ ] Deploy as cron job

### Week 3 - Onboarding Bot
- [ ] Build agent creation logic
- [ ] Build default listing creation
- [ ] Test end-to-end pipeline
- [ ] Deploy as cron job

### Week 4 - Claim System
- [ ] Build claim UI
- [ ] Build verification logic (GitHub, HF)
- [ ] Email notifications
- [ ] Admin review dashboard

**Total: 4 weeks to operational crawler system**

---

## Success Metrics

**Launch Targets (Month 1):**
- 500 agents discovered
- 100 agents onboarded
- 10 agents claimed by owners
- 5 agents generating transactions

**Year 1 Targets:**
- 10,000 agents discovered
- 2,000 agents onboarded
- 500 agents claimed
- 100 agents generating regular revenue
- Platform becomes largest agent directory

---

## Questions for Steve

1. **API Keys:** Need GitHub token, HuggingFace token - budget for paid tiers?
2. **Threshold:** 50/100 evaluation score reasonable or too low/high?
3. **Curation:** Should we manually review all before onboarding or trust automation?
4. **Notifications:** Email owners when we discover their agents?
5. **Priority:** Build this before or after acquisition feature?

---

**This crawler makes Agent Directory the "Google" of AI agents. We discover, index, and organize the entire agent ecosystem.**

🚀
