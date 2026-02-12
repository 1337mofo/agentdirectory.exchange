#!/usr/bin/env python3
"""Check what enum values exist in database"""
import sys
import psycopg2

DATABASE_URL = sys.argv[1] if len(sys.argv) > 1 else None

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Query enum type definition
    cur.execute("""
        SELECT e.enumlabel
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid  
        WHERE t.typname = 'agenttype'
        ORDER BY e.enumsortorder
    """)
    
    values = cur.fetchall()
    
    print("AgentType enum values in database:")
    for val in values:
        print(f"  - '{val[0]}'")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
