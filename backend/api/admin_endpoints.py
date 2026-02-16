"""
Admin API Endpoints - Secure database operations
Requires: Authorization: Bearer {ADMIN_API_KEY}
"""
from fastapi import APIRouter, Header, HTTPException
import os
import psycopg2
from typing import Dict, Any

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "eagle_admin_zI8_lo08WoS0xrhVUhZRNz0aj1IgEniGbJU1VEpFb54")

def verify_admin(authorization: str = Header(None)):
    """Verify admin API key"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


@router.get("/health")
async def health_check(authorization: str = Header(None)):
    """Check database connectivity"""
    verify_admin(authorization)
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        return {"status": "error", "message": "DATABASE_URL not configured"}
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "postgres_version": version
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }


@router.post("/migrate")
async def run_migrations(authorization: str = Header(None)) -> Dict[str, Any]:
    """Run database migrations"""
    verify_admin(authorization)
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    
    results = []
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Migration 1: agents table + category columns
        results.append("Ensuring agents table exists with category columns...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                owner_email VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Add category columns if they don't exist
        cursor.execute("""
            ALTER TABLE agents ADD COLUMN IF NOT EXISTS primary_use_case VARCHAR(100);
            ALTER TABLE agents ADD COLUMN IF NOT EXISTS use_case_tags TEXT[];
            ALTER TABLE agents ADD COLUMN IF NOT EXISTS skill_tags TEXT[];
            ALTER TABLE agents ADD COLUMN IF NOT EXISTS industry_tags TEXT[];
            ALTER TABLE agents ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE;
            
            CREATE INDEX IF NOT EXISTS idx_agents_primary_use_case ON agents(primary_use_case);
            CREATE INDEX IF NOT EXISTS idx_agents_use_case_tags ON agents USING GIN(use_case_tags);
            CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug);
        """)
        conn.commit()
        results.append("[OK] agents table ready with category columns")
        
        # Migration 2: categories table
        results.append("Creating agent_categories table...")
        cursor.execute("""
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
        """)
        conn.commit()
        results.append("[OK] agent_categories table created")
        
        # Migration 3: Check if categories exist
        cursor.execute("SELECT COUNT(*) FROM agent_categories")
        count = cursor.fetchone()[0]
        
        if count == 0:
            results.append(f"Inserting categories...")
            # Try to read SQL file
            try:
                with open('/app/migrations/add_100_categories.sql', 'r', encoding='utf-8') as f:
                    sql = f.read()
                    cursor.execute(sql)
                    conn.commit()
                
                cursor.execute("SELECT COUNT(*) FROM agent_categories")
                count = cursor.fetchone()[0]
                results.append(f"[OK] {count} categories inserted")
            except FileNotFoundError:
                results.append("⚠ Categories file not found (skip in local dev)")
        else:
            results.append(f"[OK] {count} categories already exist")
        
        # Migration 4: transactions table
        results.append("Creating transactions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id VARCHAR(36) PRIMARY KEY,
                buyer_agent_id VARCHAR(36),
                seller_agent_id VARCHAR(36),
                listing_id VARCHAR(36),
                amount_usd DECIMAL(10, 2),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        results.append("[OK] transactions table created")
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "Migrations completed successfully",
            "details": results
        }
        
    except Exception as e:
        results.append(f"✗ Error: {str(e)}")
        return {
            "success": False,
            "message": "Migration failed",
            "details": results,
            "error": str(e)
        }


@router.get("/status")
async def database_status(authorization: str = Header(None)):
    """Get database table status"""
    verify_admin(authorization)
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row counts
        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "tables": tables,
            "counts": counts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
