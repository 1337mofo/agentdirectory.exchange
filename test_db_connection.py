#!/usr/bin/env python3
"""Test database connection"""
import sys
import psycopg2

DATABASE_URL = sys.argv[1] if len(sys.argv) > 1 else None

if not DATABASE_URL:
    print("Usage: python test_db_connection.py [DATABASE_URL]")
    sys.exit(1)

print("Testing database connection...")
print(f"URL: {DATABASE_URL[:50]}...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Test query
    cur.execute("SELECT COUNT(*) FROM agents")
    count = cur.fetchone()[0]
    
    print(f"✓ Connection successful!")
    print(f"✓ Current agent count: {count}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
