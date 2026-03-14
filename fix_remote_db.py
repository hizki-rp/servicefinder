"""
Run this directly with: python fix_remote_db.py
Adds missing columns to the remote PostgreSQL DB.
"""
import os
import psycopg2

DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(DB_URL)
conn.autocommit = True  # Each statement commits immediately
cur = conn.cursor()

columns = [
    ("providers_providerprofile", "is_active",         "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("providers_providerprofile", "suspended_at",      "TIMESTAMP WITH TIME ZONE NULL"),
    ("providers_providerprofile", "suspension_reason", "TEXT NOT NULL DEFAULT ''"),
    ("providers_providerservice", "hidden_at",         "TIMESTAMP WITH TIME ZONE NULL"),
    ("providers_providerservice", "hidden_reason",     "TEXT NOT NULL DEFAULT ''"),
]

for table, col, col_type in columns:
    sql = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}'
    try:
        cur.execute(sql)
        print(f"  OK  : {table}.{col}")
    except Exception as e:
        print(f"  SKIP: {table}.{col} — {e}")

cur.close()
conn.close()
print("\nDone. All missing columns added.")
