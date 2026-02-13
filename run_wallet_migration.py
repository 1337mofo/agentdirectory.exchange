"""
Run wallet fields migration on Railway PostgreSQL
"""
import psycopg2
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Railway PostgreSQL connection
DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

def run_migration():
    """Execute the wallet fields migration"""
    print("=" * 70)
    print("WALLET FIELDS MIGRATION")
    print("=" * 70)
    print("\nConnecting to Railway PostgreSQL...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("✓ Connected to database")
        print("\nRunning migration...")
        
        # Read migration SQL
        with open('migrations/003_add_wallet_fields.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        cur.execute(migration_sql)
        conn.commit()
        
        print("✓ Migration completed successfully")
        
        # Verify columns were added
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'agents' 
            AND column_name IN (
                'wallet_address',
                'wallet_private_key_encrypted',
                'wallet_created_at',
                'usdc_balance',
                'last_balance_check'
            )
            ORDER BY column_name;
        """)
        
        columns = cur.fetchall()
        
        print(f"\n✓ Added {len(columns)} wallet columns:")
        for col_name, col_type in columns:
            print(f"  - {col_name} ({col_type})")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ WALLET SYSTEM READY")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Agents will auto-create wallets on registration")
        print("2. Agents can authenticate via wallet signature")
        print("3. Agents can receive USDC payments")
        print()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
