"""
Analyze existing 766 agents to determine natural category groupings
Run this BEFORE creating any category system
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from collections import Counter

load_dotenv('backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def analyze_agents():
    session = Session()
    
    try:
        # Get all agents
        result = session.execute(text("""
            SELECT id, name, description, capabilities
            FROM agents
            WHERE status = 'VERIFIED'
            ORDER BY id
        """))
        
        agents = result.fetchall()
        print(f"\n📊 Analyzing {len(agents)} verified agents...\n")
        
        # Keyword frequency analysis
        keywords = Counter()
        
        for agent in agents:
            agent_id, name, description, capabilities = agent
            text_combined = f"{name} {description or ''} {' '.join(capabilities or [])}".lower()
            
            # Extract meaningful keywords
            words = text_combined.split()
            for word in words:
                if len(word) > 4:  # Ignore short words
                    keywords[word] += 1
        
        # Top 50 keywords
        print("🔑 TOP 50 KEYWORDS IN AGENT DATA:")
        print("=" * 60)
        for word, count in keywords.most_common(50):
            print(f"{word:30} → {count:3} agents")
        
        print(f"\n✅ Analysis complete. Use these keywords to create REAL categories.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    analyze_agents()
