"""
Seed endpoint - populate sample agents for initial launch
"""
from fastapi import APIRouter, Header, HTTPException
import os
import psycopg2
import uuid
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "eagle_admin_zI8_lo08WoS0xrhVUhZRNz0aj1IgEniGbJU1VEpFb54")

def verify_admin(authorization: str = Header(None)):
    """Verify admin API key"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


# Sample agents to seed
SAMPLE_AGENTS = [
    {"name": "DataMiner Pro", "description": "Advanced data extraction and analysis agent with natural language querying", "use_case": "data-analysis"},
    {"name": "ContentCraft AI", "description": "AI-powered content generation for blogs, social media, and marketing copy", "use_case": "content-writing"},
    {"name": "CodeReviewer", "description": "Automated code review agent that identifies bugs and suggests improvements", "use_case": "code-review"},
    {"name": "CustomerSupport Bot", "description": "24/7 intelligent customer support with context-aware responses", "use_case": "customer-support"},
    {"name": "LeadQualifier", "description": "Automatically qualifies sales leads and prioritizes high-value prospects", "use_case": "lead-generation"},
    {"name": "ResearchAssistant", "description": "Academic and market research agent with citation tracking", "use_case": "market-research"},
    {"name": "EmailMarketer", "description": "Personalized email campaign creation and optimization", "use_case": "email-marketing"},
    {"name": "SocialMediaManager", "description": "Automated social media posting and engagement tracking", "use_case": "social-media"},
    {"name": "SEOOptimizer", "description": "Search engine optimization analysis and content recommendations", "use_case": "seo-content"},
    {"name": "TaskAutomator", "description": "Workflow automation agent for repetitive business tasks", "use_case": "automation"},
    {"name": "TranslationPro", "description": "Multi-language translation with context preservation", "use_case": "translation"},
    {"name": "ImageGenerator", "description": "AI image generation for marketing and creative projects", "use_case": "image-generation"},
    {"name": "VideoEditor", "description": "Automated video editing with scene detection and transitions", "use_case": "video-editing"},
    {"name": "DataVisualizer", "description": "Transforms complex data into interactive visualizations", "use_case": "data-visualization"},
    {"name": "ChatbotBuilder", "description": "Conversational AI chatbot creation platform", "use_case": "chatbot"},
    {"name": "SentimentAnalyzer", "description": "Real-time sentiment analysis of customer feedback", "use_case": "sentiment-analysis"},
    {"name": "PredictiveAnalytics", "description": "Forecasting agent for sales, inventory, and trends", "use_case": "predictive-analytics"},
    {"name": "DocumentSummarizer", "description": "Condenses long documents into key insights", "use_case": "summarization"},
    {"name": "VoiceAssistant", "description": "Voice-activated AI assistant for hands-free operations", "use_case": "voice-assistant"},
    {"name": "ComplianceChecker", "description": "Automated regulatory compliance monitoring", "use_case": "compliance"},
]

@router.post("/seed")
async def seed_agents(authorization: str = Header(None)):
    """
    Seed the database with sample agents
    One-time operation to populate initial agent listings
    """
    verify_admin(authorization)
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    
    results = []
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if agents already exist
        cursor.execute("SELECT COUNT(*) FROM agents")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            return {
                "success": False,
                "message": f"Database already has {existing_count} agents. Delete them first if you want to re-seed.",
                "existing_count": existing_count
            }
        
        # Insert sample agents
        inserted = 0
        for agent in SAMPLE_AGENTS:
            agent_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO agents (id, name, description, primary_use_case, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                agent_id,
                agent["name"],
                agent["description"],
                agent["use_case"],
                datetime.utcnow()
            ))
            inserted += 1
            results.append(f"Inserted: {agent['name']}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully seeded {inserted} agents",
            "details": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Seed failed",
            "error": str(e)
        }
