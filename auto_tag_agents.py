#!/usr/bin/env python3
"""
Auto-Tag Agents with Categories
Intelligently assigns use case categories to existing agents based on name/description
"""
import psycopg2
import re
from typing import List, Dict

DATABASE_URL = "postgresql://postgres:bACiAFKqFRqXNWwTUqxdehBJjOhMmhOK@autorack.proxy.rlwy.net:36587/railway"

# Keyword mapping for category detection
CATEGORY_KEYWORDS = {
    'agents-for-content-writing': ['content', 'writing', 'writer', 'article', 'blog', 'copy', 'text', 'content creation'],
    'agents-for-blog-writing': ['blog', 'blogging', 'blogger', 'article', 'post'],
    'agents-for-copywriting': ['copy', 'copywriting', 'copywriter', 'sales copy', 'ad copy', 'marketing copy'],
    'agents-for-social-media-posts': ['social media', 'instagram', 'facebook', 'twitter', 'linkedin', 'tiktok', 'post'],
    'agents-for-seo-content': ['seo', 'search engine', 'optimization', 'keyword', 'rank'],
    
    'agents-for-customer-support': ['customer support', 'support', 'help desk', 'service', 'ticket'],
    'agents-for-customer-service': ['customer service', 'customer care', 'service'],
    'agents-for-live-chat': ['live chat', 'chat', 'messaging', 'instant'],
    'agents-for-chatbot': ['chatbot', 'bot', 'conversational', 'dialogue'],
    'agents-for-email-support': ['email support', 'email service'],
    
    'agents-for-lead-generation': ['lead', 'leads', 'prospecting', 'lead gen', 'outreach'],
    'agents-for-email-marketing': ['email marketing', 'newsletter', 'campaign'],
    'agents-for-sales-automation': ['sales', 'selling', 'sales automation', 'crm'],
    'agents-for-marketing-automation': ['marketing', 'automation', 'campaign'],
    
    'agents-for-data-analysis': ['data analysis', 'analytics', 'analyze', 'data science'],
    'agents-for-market-research': ['market research', 'research', 'competitive', 'intelligence'],
    'agents-for-web-scraping': ['scraping', 'scraper', 'crawling', 'extraction'],
    
    'agents-for-coding': ['coding', 'programming', 'developer', 'code', 'software', 'development'],
    'agents-for-python-coding': ['python', 'py'],
    'agents-for-javascript-coding': ['javascript', 'js', 'node', 'react'],
    'agents-for-testing': ['testing', 'test', 'qa', 'quality assurance'],
    'agents-for-debugging': ['debug', 'debugging', 'bug', 'error', 'fix'],
    
    'agents-for-workflow-automation': ['workflow', 'automation', 'automate', 'process'],
    'agents-for-task-management': ['task', 'todo', 'productivity', 'project'],
    'agents-for-scheduling': ['schedule', 'calendar', 'appointment', 'booking'],
    
    'agents-for-graphic-design': ['design', 'graphic', 'visual', 'creative'],
    'agents-for-image-generation': ['image', 'picture', 'photo', 'generation', 'ai art'],
    'agents-for-video-editing': ['video', 'editing', 'video editing'],
}

def normalize_text(text: str) -> str:
    """Normalize text for matching"""
    if not text:
        return ""
    return text.lower().strip()

def detect_categories(name: str, description: str) -> List[str]:
    """Detect appropriate categories for an agent"""
    text = f"{normalize_text(name)} {normalize_text(description)}"
    
    matches = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                if category not in matches:
                    matches.append(category)
                    break  # Found one keyword for this category, move to next
    
    # Default to general if no matches
    if not matches:
        matches = ['agents-for-virtual-assistant']  # Generic fallback
    
    return matches[:3]  # Max 3 categories per agent

def generate_slug(agent_id: str, name: str) -> str:
    """Generate URL-friendly slug for agent"""
    # Use first 8 chars of ID for uniqueness
    short_id = str(agent_id)[:8]
    return f"a/{short_id}"

def auto_tag_agents():
    """Main function to auto-tag all agents"""
    try:
        print("[INFO] Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("[OK] Connected!")
        
        # Get all agents without categories
        print("[INFO] Fetching agents...")
        cur.execute("""
            SELECT id, name, description, capabilities
            FROM agents
            WHERE primary_use_case IS NULL OR primary_use_case = ''
            ORDER BY created_at DESC
        """)
        
        agents = cur.fetchall()
        print(f"[INFO] Found {len(agents)} agents to tag")
        
        tagged_count = 0
        
        for agent in agents:
            agent_id, name, description, capabilities = agent
            
            # Detect categories
            categories = detect_categories(name, description)
            primary_category = categories[0]
            
            # Generate slug
            slug = generate_slug(agent_id, name)
            
            # Update agent
            try:
                cur.execute("""
                    UPDATE agents 
                    SET 
                        primary_use_case = %s,
                        use_case_tags = %s,
                        slug = %s
                    WHERE id = %s
                """, (primary_category, categories, slug, agent_id))
                
                conn.commit()
                tagged_count += 1
                
                if tagged_count % 50 == 0:
                    print(f"[INFO] Tagged {tagged_count} agents...")
                    
            except Exception as e:
                print(f"[WARN] Failed to tag agent {agent_id}: {str(e)[:100]}")
                conn.rollback()
                continue
        
        print(f"\n[SUCCESS] Tagged {tagged_count} agents!")
        
        # Show category distribution
        print("\n[INFO] Category distribution:")
        cur.execute("""
            SELECT primary_use_case, COUNT(*) as count
            FROM agents
            WHERE primary_use_case IS NOT NULL
            GROUP BY primary_use_case
            ORDER BY count DESC
            LIMIT 20
        """)
        
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} agents")
        
        # Refresh materialized view
        print("\n[INFO] Refreshing category stats...")
        cur.execute("REFRESH MATERIALIZED VIEW category_stats")
        conn.commit()
        print("[OK] Stats refreshed!")
        
        cur.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Auto-tagging failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = auto_tag_agents()
    sys.exit(0 if success else 1)
