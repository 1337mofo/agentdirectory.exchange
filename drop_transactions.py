import psycopg2
conn = psycopg2.connect("postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS transactions CASCADE")
conn.commit()
print("Dropped transactions table")
conn.close()
