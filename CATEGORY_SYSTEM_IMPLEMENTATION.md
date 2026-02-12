# Category System Implementation Plan
**Date:** 2026-02-12  
**Objective:** Build category pages matching high-volume agent search terms

## Database Schema Changes

### Add Tags/Categories to Agents Table

```sql
-- Add new columns to agents table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS primary_use_case VARCHAR(100);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS use_case_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS skill_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS industry_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_primary_use_case ON agents(primary_use_case);
CREATE INDEX IF NOT EXISTS idx_agents_use_case_tags ON agents USING GIN(use_case_tags);
CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug);

-- Create categories reference table
CREATE TABLE IF NOT EXISTS agent_categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    search_volume INT DEFAULT 0,
    icon VARCHAR(100),
    parent_category VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Seed Top 20 Categories

```sql
INSERT INTO agent_categories (slug, name, description, search_volume, parent_category) VALUES
-- Content Creation
('agents-for-content-writing', 'Content Writing', 'AI agents specialized in creating written content', 10000, 'content'),
('agents-for-blog-writing', 'Blog Writing', 'AI agents for writing blog posts and articles', 8000, 'content'),
('agents-for-social-media', 'Social Media Management', 'AI agents for creating and managing social media content', 9000, 'content'),
('agents-for-copywriting', 'Copywriting', 'AI agents for sales copy, ads, and marketing content', 7000, 'content'),
('agents-for-seo-content', 'SEO Content', 'AI agents for search-optimized content creation', 6000, 'content'),

-- Customer Experience
('agents-for-customer-support', 'Customer Support', 'AI agents for handling customer inquiries and support tickets', 12000, 'customer'),
('agents-for-live-chat', 'Live Chat', 'AI agents for real-time customer chat support', 8000, 'customer'),
('agents-for-email-support', 'Email Support', 'AI agents for managing customer email communications', 6000, 'customer'),

-- Marketing & Sales
('agents-for-lead-generation', 'Lead Generation', 'AI agents for finding and qualifying sales leads', 11000, 'marketing'),
('agents-for-email-marketing', 'Email Marketing', 'AI agents for email campaign creation and management', 9000, 'marketing'),
('agents-for-sales-automation', 'Sales Automation', 'AI agents for automating sales workflows', 7000, 'marketing'),

-- Data & Research
('agents-for-data-analysis', 'Data Analysis', 'AI agents for analyzing and interpreting data', 10000, 'data'),
('agents-for-market-research', 'Market Research', 'AI agents for market analysis and competitive intelligence', 8000, 'data'),
('agents-for-web-scraping', 'Web Scraping', 'AI agents for extracting data from websites', 7000, 'data'),

-- Development
('agents-for-coding', 'Coding & Development', 'AI agents for writing and reviewing code', 11000, 'development'),
('agents-for-testing', 'Software Testing', 'AI agents for automated testing and QA', 6000, 'development'),
('agents-for-debugging', 'Debugging', 'AI agents for finding and fixing code issues', 5000, 'development'),

-- Operations
('agents-for-workflow-automation', 'Workflow Automation', 'AI agents for automating business processes', 9000, 'operations'),
('agents-for-task-management', 'Task Management', 'AI agents for organizing and tracking tasks', 6000, 'operations'),
('agents-for-scheduling', 'Scheduling', 'AI agents for calendar and appointment management', 5000, 'operations');
```

## API Endpoints (New)

### GET /categories
List all agent categories

**Response:**
```json
{
  "categories": [
    {
      "slug": "agents-for-content-writing",
      "name": "Content Writing",
      "description": "AI agents specialized in creating written content",
      "agent_count": 45
    }
  ]
}
```

### GET /category/{slug}
Get category details and agents

**Example:** `/category/agents-for-content-writing`

**Response:**
```json
{
  "category": {
    "slug": "agents-for-content-writing",
    "name": "Content Writing",
    "description": "AI agents specialized in creating written content",
    "parent_category": "content"
  },
  "agents": [
    {
      "id": "uuid",
      "name": "ContentBot Pro",
      "description": "Professional content writing agent",
      "slug": "a/xk9m",
      "rating_avg": 4.7,
      "transaction_count": 234,
      "capabilities": ["blog_posts", "articles", "seo"],
      "pricing_start": 49.99
    }
  ],
  "total_agents": 45,
  "related_categories": [
    {"slug": "agents-for-blog-writing", "name": "Blog Writing"},
    {"slug": "agents-for-seo-content", "name": "SEO Content"}
  ]
}
```

### GET /agents/search
Search agents with filters

**Parameters:**
- `use_case`: Filter by primary use case
- `skills`: Filter by skill tags (comma-separated)
- `industry`: Filter by industry
- `min_rating`: Minimum rating
- `max_price`: Maximum price
- `sort`: Sort by (rating, price, popularity, newest)

## Frontend Pages

### Category Page Template
**File:** `frontend/category.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Best AI Agents for {{category.name}} | Agent Directory Exchange</title>
    <meta name="description" content="Find the best AI agents for {{category.name}}. Compare {{agent_count}} specialized agents, read reviews, and hire the perfect solution.">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/">Agent Directory Exchange</a>
            <a href="/categories">Browse Categories</a>
            <a href="/about">About</a>
        </nav>
    </header>
    
    <main class="category-page">
        <div class="hero">
            <h1>Best AI Agents for {{category.name}}</h1>
            <p class="subtitle">{{agent_count}} specialized agents ready to help</p>
            <p class="description">{{category.description}}</p>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <label>Sort by:</label>
                <select id="sort">
                    <option value="rating">Highest Rated</option>
                    <option value="popularity">Most Popular</option>
                    <option value="price-low">Price: Low to High</option>
                    <option value="price-high">Price: High to Low</option>
                    <option value="newest">Newest First</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Price Range:</label>
                <input type="range" id="max-price" min="0" max="500" value="500">
                <span id="price-display">Up to $500/mo</span>
            </div>
            
            <div class="filter-group">
                <label>Minimum Rating:</label>
                <select id="min-rating">
                    <option value="0">Any</option>
                    <option value="3">3+ Stars</option>
                    <option value="4">4+ Stars</option>
                    <option value="4.5">4.5+ Stars</option>
                </select>
            </div>
        </div>
        
        <div class="agent-grid">
            {{#each agents}}
            <div class="agent-card">
                <div class="agent-header">
                    <h3>{{this.name}}</h3>
                    <div class="rating">
                        <span class="stars">⭐ {{this.rating_avg}}</span>
                        <span class="reviews">({{this.transaction_count}} hires)</span>
                    </div>
                </div>
                
                <p class="agent-description">{{this.description}}</p>
                
                <div class="agent-capabilities">
                    {{#each this.capabilities}}
                    <span class="capability-tag">{{this}}</span>
                    {{/each}}
                </div>
                
                <div class="agent-footer">
                    <span class="price">From ${{this.pricing_start}}/mo</span>
                    <a href="/{{this.slug}}" class="btn-primary">View Details</a>
                </div>
            </div>
            {{/each}}
        </div>
        
        <div class="related-categories">
            <h2>Related Categories</h2>
            <div class="category-links">
                {{#each related_categories}}
                <a href="/{{this.slug}}" class="category-link">
                    {{this.name}} →
                </a>
                {{/each}}
            </div>
        </div>
        
        <div class="cta-section">
            <h2>Can't find what you need?</h2>
            <p>Submit a request and we'll help you find the perfect agent</p>
            <a href="/contact" class="btn-secondary">Request Agent</a>
        </div>
    </main>
    
    <footer>
        <p>© 2026 Agent Directory Exchange. All rights reserved.</p>
    </footer>
    
    <script src="/static/category.js"></script>
</body>
</html>
```

### Category Listing Page
**File:** `frontend/categories.html`

Lists all categories with agent counts and descriptions.

## Implementation Steps

### Phase 1: Database & Backend (Day 1)
1. ✅ Run SQL migrations (add columns, create categories table, seed data)
2. ✅ Create `/categories` API endpoint
3. ✅ Create `/category/{slug}` API endpoint
4. ✅ Create `/agents/search` API endpoint with filters

### Phase 2: Agent Tagging (Day 1-2)
1. Tag existing 766 agents with appropriate categories
2. Generate slugs for individual agent pages
3. Assign primary_use_case to each agent
4. Add skill_tags and industry_tags where applicable

### Phase 3: Frontend (Day 2-3)
1. Create category page template
2. Create categories listing page
3. Add category navigation to homepage
4. Add filtering/sorting JavaScript
5. Style with CSS

### Phase 4: SEO (Day 3-4)
1. Add meta tags to each category page
2. Create sitemap with all category URLs
3. Add structured data (Schema.org)
4. Submit to search engines

### Phase 5: Testing & Launch (Day 4-5)
1. Test all category pages load correctly
2. Test filtering/sorting works
3. Test mobile responsiveness
4. Deploy to production

## Auto-Tagging Strategy for 766 Existing Agents

Use agent names and descriptions to auto-assign categories:

**Keywords → Category Mapping:**
```python
CATEGORY_KEYWORDS = {
    "content_writing": ["content", "writing", "writer", "article", "blog", "copy"],
    "customer_support": ["support", "customer", "help", "service", "chat"],
    "data_analysis": ["data", "analysis", "analytics", "insights", "report"],
    "coding": ["code", "developer", "programming", "python", "javascript"],
    "marketing": ["marketing", "seo", "email", "campaign", "advertising"],
    "research": ["research", "market", "competitive", "intelligence"],
    # etc.
}
```

Run script to analyze each agent's name/description and assign top 2-3 matching categories.

## Success Metrics (Track After Launch)

**Per Category:**
- Page views
- Unique visitors
- Bounce rate
- Conversion rate (view → agent page click)
- Average time on page

**Overall:**
- Organic search traffic to category pages
- Category page → agent page conversion
- Category page → transaction conversion
- Most popular categories (guide future expansion)

---

**Timeline:** 5 days from start to launch  
**Priority:** HIGH (Steve requested this specifically)

**Next Immediate Steps:**
1. Write database migration SQL
2. Implement category API endpoints in FastAPI
3. Auto-tag existing 766 agents
4. Build category page template
5. Deploy top 20 categories

**Nova Eagle - AI Project Lead**
