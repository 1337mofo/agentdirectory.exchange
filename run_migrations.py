"""Run migrations using DATABASE_URL from Railway environment"""
import psycopg2
import sys
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print("="*70)
print("RUNNING MIGRATIONS")
print("="*70)

try:
    print("\n[*] Connecting...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("[OK] Connected!\n")
    
    print("[1/4] Creating agents table...")
    cursor.execute("""
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
    """)
    conn.commit()
    print("      [OK]\n")
    
    print("[2/4] Creating categories table...")
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
    print("      [OK]\n")
    
    print("[3/4] Inserting 100 categories...")
    with open('migrations/add_100_categories.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        cursor.execute(sql)
        conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM agent_categories;")
    count = cursor.fetchone()[0]
    print(f"      [OK] {count} categories\n")
    
    print("[4/4] Creating transactions table...")
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
    print("      [OK]\n")
    
    cursor.close()
    conn.close()
    
    print("="*70)
    print("SUCCESS!")
    print("="*70)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
