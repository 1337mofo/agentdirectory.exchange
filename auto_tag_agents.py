"""
Auto-Tag Existing Agents with Categories
Agent Directory Exchange
Assigns primary_use_case and use_case_tags based on keyword matching
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment
load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Category keyword mapping (from TOP_100_AGENT_SEARCH_TERMS.md)
CATEGORY_KEYWORDS = {
    'agents-for-customer-support': ['customer support', 'support ticket', 'helpdesk', 'customer service', 'help desk'],
    'agents-for-coding': ['code', 'coding', 'programming', 'developer', 'development', 'software engineer'],
    'agents-for-lead-generation': ['lead generation', 'lead gen', 'prospecting', 'sales leads', 'lead qualify'],
    'agents-for-content-writing': ['content writing', 'content creator', 'blog writing', 'article writing', 'writer'],
    'agents-for-data-analysis': ['data analysis', 'data analytics', 'data scientist', 'analytics', 'analyze data'],
    'agents-for-workflow-automation': ['workflow automation', 'process automation', 'automate workflow', 'business automation'],
    'agents-for-social-media-posts': ['social media', 'social post', 'instagram', 'twitter', 'facebook', 'tiktok'],
    'agents-for-email-marketing': ['email marketing', 'email campaign', 'marketing email', 'newsletter'],
    'agents-for-blog-writing': ['blog', 'blogger', 'blog post', 'blog article'],
    'agents-for-live-chat': ['live chat', 'chat support', 'real-time chat', 'chatbot'],
    'agents-for-market-research': ['market research', 'market analysis', 'competitive intelligence', 'market insight'],
    'agents-for-copywriting': ['copywriting', 'copywriter', 'sales copy', 'ad copy', 'marketing copy'],
    'agents-for-sales-automation': ['sales automation', 'sales workflow', 'automate sales', 'sales process'],
    'agents-for-web-scraping': ['web scraping', 'scraping', 'data scraping', 'web crawler', 'scraper'],
    'agents-for-chatbot': ['chatbot', 'chat bot', 'conversational ai', 'chat assistant'],
    'agents-for-virtual-assistant': ['virtual assistant', 'va', 'personal assistant', 'executive assistant'],
    'agents-for-marketing-automation': ['marketing automation', 'automate marketing', 'marketing workflow'],
    'agents-for-seo-content': ['seo', 'search engine optimization', 'seo content', 'seo writing', 'organic search'],
    'agents-for-research': ['research', 'researcher', 'research assistant', 'data gathering'],
    'agents-for-testing': ['testing', 'qa', 'quality assurance', 'test automation', 'software testing'],
    'agents-for-task-management': ['task management', 'task manager', 'to-do', 'task tracking'],
    'agents-for-image-generation': ['image generation', 'generate image', 'image creator', 'ai art', 'image ai'],
    'agents-for-competitive-analysis': ['competitive analysis', 'competitor research', 'competition analysis'],
    'agents-for-helpdesk': ['helpdesk', 'help desk', 'support desk', 'ticket system'],
    'agents-for-debugging': ['debugging', 'debug', 'bug fixing', 'troubleshooting'],
    'agents-for-scheduling': ['scheduling', 'calendar', 'appointment', 'meeting scheduler'],
    'agents-for-email-copywriting': ['email copy', 'email writing', 'email template'],
    'agents-for-graphic-design': ['graphic design', 'designer', 'visual design', 'graphics'],
    'agents-for-project-management': ['project management', 'project manager', 'pm', 'project tracking'],
    'agents-for-cold-outreach': ['cold outreach', 'cold email', 'cold calling', 'outbound sales'],
    'agents-for-product-descriptions': ['product description', 'product copy', 'ecommerce copy'],
    'agents-for-video-editing': ['video editing', 'video editor', 'video production', 'video post-production'],
    'agents-for-ad-copy': ['ad copy', 'advertising', 'ppc', 'google ads', 'facebook ads'],
    'agents-for-data-entry': ['data entry', 'data input', 'data processing'],
    'agents-for-video-scripts': ['video script', 'script writing', 'screenplay', 'storyboard'],
    'agents-for-python-coding': ['python', 'python developer', 'python programming', 'python code'],
    'agents-for-financial-analysis': ['financial analysis', 'finance', 'financial data', 'fintech'],
    'agents-for-linkedin-posts': ['linkedin post', 'linkedin content', 'linkedin'],
    'agents-for-linkedin-outreach': ['linkedin outreach', 'linkedin prospecting', 'linkedin sales'],
    'agents-for-meeting-notes': ['meeting notes', 'note taking', 'meeting summary', 'transcription'],
    'agents-for-photo-editing': ['photo editing', 'photo editor', 'image editing', 'photoshop'],
    'agents-for-technical-writing': ['technical writing', 'technical documentation', 'technical writer'],
    'agents-for-javascript-coding': ['javascript', 'js', 'typescript', 'react', 'node.js'],
    'agents-for-code-review': ['code review', 'code audit', 'peer review', 'code quality'],
    'agents-for-bookkeeping': ['bookkeeping', 'accounting', 'quickbooks', 'financial records'],
}

def find_matching_categories(agent_name, agent_description):
    """
    Find all matching categories based on keywords in name/description
    Returns: (primary_use_case, [use_case_tags])
    """
    name_lower = (agent_name or '').lower()
    desc_lower = (agent_description or '').lower()
    combined = f"{name_lower} {desc_lower}"
    
    matches = []
    
    for category_slug, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined:
                matches.append(category_slug)
                break  # Count each category only once
    
    if not matches:
        return None, []
    
    # Primary = first match, tags = all matches
    return matches[0], matches

def tag_all_agents():
    """
    Tag all existing agents with categories based on keyword matching
    """
    session = Session()
    
    try:
        # Fetch all agents
        result = session.execute(text("""
            SELECT id, name, description, primary_use_case 
            FROM agents 
            WHERE status = 'VERIFIED'
            ORDER BY id
        """))
        
        agents = result.fetchall()
        print(f"\n📊 Found {len(agents)} verified agents to tag")
        
        tagged_count = 0
        skipped_count = 0
        
        for agent in agents:
            agent_id, name, description, existing_primary = agent
            
            # Find matching categories
            primary_use_case, use_case_tags = find_matching_categories(name, description)
            
            if primary_use_case:
                # Update agent with categories
                session.execute(text("""
                    UPDATE agents 
                    SET primary_use_case = :primary,
                        use_case_tags = :tags
                    WHERE id = :agent_id
                """), {
                    'primary': primary_use_case,
                    'tags': use_case_tags,
                    'agent_id': agent_id
                })
                
                tagged_count += 1
                print(f"✅ Tagged: {name[:50]} → {primary_use_case} ({len(use_case_tags)} tags)")
            else:
                skipped_count += 1
                print(f"⏭️  Skipped: {name[:50]} (no matching keywords)")
        
        # Commit all changes
        session.commit()
        
        print(f"\n✅ Auto-tagging complete!")
        print(f"   Tagged: {tagged_count} agents")
        print(f"   Skipped: {skipped_count} agents (no matches)")
        
        # Show category distribution
        print(f"\n📊 Category Distribution:")
        result = session.execute(text("""
            SELECT primary_use_case, COUNT(*) as count
            FROM agents
            WHERE primary_use_case IS NOT NULL
            GROUP BY primary_use_case
            ORDER BY count DESC
            LIMIT 20
        """))
        
        for row in result:
            category, count = row
            print(f"   {category}: {count} agents")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    print("🏷️  Agent Auto-Tagging System")
    print("=" * 60)
    tag_all_agents()
