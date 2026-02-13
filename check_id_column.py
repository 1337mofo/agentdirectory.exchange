import psycopg2

DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type, column_default, is_nullable
    FROM information_schema.columns 
    WHERE table_name='agents' 
    AND column_name='id'
""")

result = cur.fetchone()
print(f"Column: {result[0]}")
print(f"Type: {result[1]}")
print(f"Default: {result[2]}")
print(f"Nullable: {result[3]}")

conn.close()
