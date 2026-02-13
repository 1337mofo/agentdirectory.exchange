"""
Run Lightning Network support migration
"""
import psycopg2
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

def run_migration():
    print("=" * 70)
    print("LIGHTNING NETWORK MIGRATION")
    print("=" * 70)
    print("\nConnecting to database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("✓ Connected")
        print("\nRunning migration...")
        
        with open('migrations/005_add_lightning_support.sql', 'r') as f:
            migration_sql = f.read()
        
        cur.execute(migration_sql)
        conn.commit()
        
        print("✓ Migration completed")
        
        # Verify columns added
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'agents' 
            AND column_name LIKE 'lightning%'
            ORDER BY column_name;
        """)
        
        agent_cols = cur.fetchall()
        
        print(f"\n✓ Added {len(agent_cols)} Lightning columns to agents:")
        for col_name, col_type in agent_cols:
            print(f"  - {col_name} ({col_type})")
        
        # Verify transaction columns
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name IN ('payment_method', 'lightning_payment_hash', 'lightning_invoice', 'btc_amount')
            ORDER BY column_name;
        """)
        
        tx_cols = cur.fetchall()
        
        print(f"\n✓ Added {len(tx_cols)} columns to transactions:")
        for col_name, col_type in tx_cols:
            print(f"  - {col_name} ({col_type})")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ LIGHTNING NETWORK READY")
        print("=" * 70)
        print("\nAgents can now:")
        print("- Receive Bitcoin via Lightning Network")
        print("- Choose between USDC (Solana) or BTC (Lightning)")
        print("- Instant settlement on both networks")
        print("\n🚀 Built on Bitcoin + Solana")
        print()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
