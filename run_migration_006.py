"""
Run Migration 006: Agent Messaging System
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not found in environment")
    print("Set it in backend/.env or export it")
    exit(1)

print("Running Migration 006: Agent Messaging System")
print(f"Database: {DATABASE_URL[:30]}...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Read migration file
    with open("migrations/006_add_agent_messaging.sql", "r") as f:
        sql = f.read()
    
    # Execute migration
    cursor.execute(sql)
    conn.commit()
    
    # Verify tables were created
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'agent_messages', 
            'agent_presence', 
            'work_orders', 
            'agent_channels', 
            'channel_memberships'
        )
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    
    print("\nMigration completed successfully!")
    print(f"\nTables created: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Count indexes
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pg_indexes 
        WHERE tablename IN (
            'agent_messages', 
            'agent_presence', 
            'work_orders', 
            'channel_memberships'
        )
    """)
    index_count = cursor.fetchone()[0]
    print(f"\nIndexes created: {index_count}")
    
    cursor.close()
    conn.close()
    
    print("\nAgent messaging system is ready!")
    print("Next step: Restart backend to load new API routes")
    print("API docs: https://agentdirectory.exchange/docs")
    
except psycopg2.Error as e:
    print(f"\nMigration failed: {e}")
    exit(1)
except FileNotFoundError:
    print("\nMigration file not found: migrations/006_add_agent_messaging.sql")
    print("Run this script from the agentdirectory.exchange root directory")
    exit(1)
