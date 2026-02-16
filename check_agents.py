"""Check what agents exist in the database"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# Find SIBYSI/Eagle agents
cursor.execute("""
    SELECT id, name, description 
    FROM agents 
    WHERE name ILIKE '%eagle%' 
       OR name ILIKE '%sibysi%' 
       OR name ILIKE '%cost%' 
       OR name ILIKE '%niche%'
       OR name ILIKE '%scout%'
    LIMIT 20
""")

agents = cursor.fetchall()
print(f"Found {len(agents)} agents:")
for i, agent in enumerate(agents, 1):
    print(f"{i}. {agent[1]}")
    print(f"   ID: {agent[0]}")
    print(f"   Description: {agent[2][:100] if agent[2] else 'N/A'}...")
    print()

cursor.close()
conn.close()
