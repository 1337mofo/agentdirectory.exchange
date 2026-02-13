"""
Admin Migration Endpoint
Allows running database migrations via HTTP POST with admin API key
"""
from fastapi import APIRouter, Header, HTTPException
import os
from sqlalchemy import text
from database.base import get_db_engine

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "eagle_admin_zI8_lo08WoS0xrhVUhZRNz0aj1IgEniGbJU1VEpFb54")

@router.post("/migrate")
async def run_migrations(authorization: str = Header(None)):
    """
    Run database migrations
    Requires: Authorization: Bearer {ADMIN_API_KEY}
    """
    # Validate API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    engine = get_db_engine()
    results = []
    
    try:
        with engine.connect() as conn:
            # Migration 1: Create agents table
            results.append("Creating agents table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agents (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    owner_email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT NOW(),
                    primary_use_case VARCHAR(100),
                    use_case_tags TEXT[],
                    skill_tags TEXT[],
                    industry_tags TEXT[],
                    slug VARCHAR(255) UNIQUE
                );
                
                CREATE INDEX IF NOT EXISTS idx_agents_primary_use_case ON agents(primary_use_case);
                CREATE INDEX IF NOT EXISTS idx_agents_use_case_tags ON agents USING GIN(use_case_tags);
                CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug);
            """))
            conn.commit()
            results.append("✅ Agents table created")
            
            # Migration 2: Create categories table
            results.append("Creating agent_categories table...")
            conn.execute(text("""
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
            """))
            conn.commit()
            results.append("✅ Categories table created")
            
            # Migration 3: Read and run 100 categories SQL
            results.append("Loading 100 categories...")
            with open('/app/migrations/add_100_categories.sql', 'r', encoding='utf-8') as f:
                categories_sql = f.read()
                conn.execute(text(categories_sql))
                conn.commit()
            
            # Count categories
            result = conn.execute(text("SELECT COUNT(*) FROM agent_categories;"))
            count = result.scalar()
            results.append(f"✅ {count} categories inserted")
            
            # Migration 4: Create transactions table
            results.append("Creating transactions table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id VARCHAR(36) PRIMARY KEY,
                    buyer_agent_id VARCHAR(36),
                    seller_agent_id VARCHAR(36),
                    listing_id VARCHAR(36),
                    amount_usd DECIMAL(10, 2),
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """))
            conn.commit()
            results.append("✅ Transactions table created")
            
        return {
            "success": True,
            "message": "All migrations completed successfully",
            "details": results
        }
        
    except Exception as e:
        results.append(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "message": "Migration failed",
            "details": results,
            "error": str(e)
        }
