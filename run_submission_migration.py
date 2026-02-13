"""
Run submission fields migration on Railway PostgreSQL
"""
import psycopg2
import os

# Railway PostgreSQL connection
DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

def run_migration():
    """Execute the submission fields migration"""
    print("🔄 Connecting to Railway PostgreSQL...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("✓ Connected to database")
        print("🔄 Running migration...")
        
        # Read migration SQL
        with open('migrations/002_add_submission_fields.sql', 'r') as f:
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
                'pending_review', 
                'submission_source', 
                'auto_discovered', 
                'approved_at', 
                'rejected_at', 
                'rejection_reason',
                'verified',
                'source_url',
                'categories'
            )
            ORDER BY column_name;
        """)
        
        columns = cur.fetchall()
        
        print(f"\n✓ Added {len(columns)} new columns:")
        for col_name, col_type in columns:
            print(f"  - {col_name} ({col_type})")
        
        conn.close()
        print("\n✅ Submission system ready!")
        print("📝 Users can now submit agents at /submit-agent.html")
        print("👀 Review submissions at /api/v1/agents/submissions/pending")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
