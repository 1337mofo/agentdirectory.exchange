#!/usr/bin/env python3
import sys
import psycopg2

DATABASE_URL = sys.argv[1] if len(sys.argv) > 1 else None

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM agents")
    count = cur.fetchone()[0]
    
    print(f"Total agents in database: {count}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
