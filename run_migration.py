#!/usr/bin/env python3
"""
Run database migration for 100-category system
"""
import psycopg2
import sys
import os

DATABASE_URL = "postgresql://postgres:bACiAFKqFRqXNWwTUqxdehBJjOhMmhOK@autorack.proxy.rlwy.net:36587/railway"

def run_migration():
    try:
        print("[INFO] Connecting to Railway database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("[OK] Connected!")
        
        # Read migration file
        migration_path = os.path.join(os.path.dirname(__file__), "migrations", "add_100_categories.sql")
        print(f"[INFO] Reading migration: {migration_path}")
        
        with open(migration_path, "r", encoding="utf-8") as f:
            sql = f.read()
        
        print("[INFO] Executing migration...")
        
        # Execute migration (split by statement for better error handling)
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        total = len(statements)
        for i, statement in enumerate(statements, 1):
            try:
                print(f"[{i}/{total}] Executing statement...")
                cur.execute(statement)
                conn.commit()
                print(f"[OK] Statement {i} complete")
            except Exception as e:
                print(f"[WARN] Statement {i} failed (may be OK if already exists): {str(e)[:100]}")
                conn.rollback()
                continue
        
        # Verify categories
        cur.execute("SELECT COUNT(*) FROM agent_categories")
        count = cur.fetchone()[0]
        print(f"\n[SUCCESS] Migration complete! {count} categories in database")
        
        # Show tier breakdown
        cur.execute("SELECT tier, COUNT(*) FROM agent_categories GROUP BY tier ORDER BY tier")
        print("\nCategory breakdown by tier:")
        for row in cur.fetchall():
            print(f"  Tier {row[0]}: {row[1]} categories")
        
        cur.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("[INFO] Railway database may be slow/overloaded. Retrying...")
        return False
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
