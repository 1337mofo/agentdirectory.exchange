"""
Run transactions table migration
"""
import psycopg2
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

def check_agents_table():
    """Check agents table structure"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'agents' 
        AND column_name = 'id'
    """)
    
    result = cur.fetchone()
    conn.close()
    return result

def run_migration():
    """Execute transactions table migration"""
    print("=" * 70)
    print("TRANSACTIONS TABLE MIGRATION")
    print("=" * 70)
    
    # Check agents table first
    print("\nChecking agents table structure...")
    id_col = check_agents_table()
    
    if not id_col:
        print("✗ Error: agents table has no 'id' column!")
        return
    
    print(f"✓ agents.id exists: {id_col[0]} ({id_col[1]})")
    
    print("\nConnecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("✓ Connected")
    print("\nRunning migration...")
    
    try:
        with open('migrations/004_add_transactions_table.sql', 'r') as f:
            migration_sql = f.read()
        
        cur.execute(migration_sql)
        conn.commit()
        
        print("✓ Migration completed")
        
        # Verify table created
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'transactions'
        """)
        
        if cur.fetchone()[0] > 0:
            print("✓ transactions table created successfully")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ TRANSACTION LOGGING READY")
        print("=" * 70)
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        conn.close()
        raise

if __name__ == "__main__":
    run_migration()
