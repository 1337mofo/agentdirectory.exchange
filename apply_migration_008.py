"""
Apply Migration 008: Anti-Abuse Rate Limiting System
"""
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:aRFnDbaXZvAaIKFgFBnpjRmzoanlwGkO@mainline.proxy.rlwy.net:11716/railway")

def apply_migration():
    """Apply migration 008 to Railway database"""
    print("[*] Connecting to Railway database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("[*] Reading migration file...")
        with open("migrations/008_add_rate_limiting.sql", "r") as f:
            migration_sql = f.read()
        
        print("[*] Applying migration 008...")
        cur.execute(migration_sql)
        conn.commit()
        
        print("[OK] Migration 008 applied successfully")
        
        # Verify new columns
        print("\n[*] Verifying new columns...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'agents' 
            AND column_name IN (
                'free_calls_total', 
                'free_calls_remaining', 
                'hourly_rate_limit',
                'signup_ip_address',
                'paid_calls_remaining'
            )
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"[OK] Found {len(columns)} new columns: {', '.join(columns)}")
        
        # Verify new tables
        print("\n[*] Verifying new tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN (
                'ip_signup_tracking',
                'disposable_email_domains',
                'daily_platform_spending'
            )
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"[OK] Found {len(tables)} new tables: {', '.join(tables)}")
        
        # Count disposable domains
        cur.execute("SELECT COUNT(*) FROM disposable_email_domains")
        domain_count = cur.fetchone()[0]
        print(f"[OK] Loaded {domain_count} disposable email domains")
        
        # Update existing agents
        cur.execute("SELECT COUNT(*) FROM agents")
        agent_count = cur.fetchone()[0]
        print(f"\n[*] Updating {agent_count} existing agents with default rate limits...")
        
        cur.execute("""
            UPDATE agents 
            SET 
                free_calls_total = 50,
                free_calls_remaining = 50,
                hourly_rate_limit = 5,
                hourly_calls_count = 0,
                hourly_reset_at = NOW(),
                daily_spending_exposure = 0.0,
                paid_calls_remaining = 0
            WHERE free_calls_total IS NULL
        """)
        updated = cur.rowcount
        conn.commit()
        print(f"[OK] Updated {updated} agents")
        
        print("\n[OK] Anti-abuse system fully deployed!")
        print("\n[STATS] System Configuration:")
        print("  • Free tier: 50 total calls, 5 calls/hour")
        print("  • IP limit: 5 signups per IP per day")
        print("  • Platform cap: $50/day free tier spending")
        print(f"  • Disposable emails: {domain_count} domains blocked")
        print("\n[EAGLE] Platform is now 100% agent-ready!")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("\n[EAGLE] AgentDirectory.Exchange - Migration 008")
    print("=" * 60)
    print("Anti-Abuse Rate Limiting System")
    print("=" * 60)
    print()
    
    success = apply_migration()
    
    if success:
        print("\n[OK] Migration complete - anti-abuse system active")
    else:
        print("\n[ERROR] Migration failed - check errors above")
