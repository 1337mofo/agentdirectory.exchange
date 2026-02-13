import psycopg2

DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

print("Connecting to Railway database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Adding source_url column...")
cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS source_url TEXT")

print("Creating index...")
cur.execute("CREATE INDEX IF NOT EXISTS idx_agents_source_url ON agents(source_url)")

conn.commit()

print("Schema updated successfully!")

# Verify
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'agents' ORDER BY ordinal_position")
columns = [row[0] for row in cur.fetchall()]

print(f"\nTable 'agents' now has {len(columns)} columns:")
for col in columns:
    print(f"  - {col}")

conn.close()
print("\nDone!")
