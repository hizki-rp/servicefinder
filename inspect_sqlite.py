#!/usr/bin/env python3
"""
Inspect SQLite database contents.
"""
import sqlite3
from pathlib import Path

def inspect_sqlite():
    sqlite_path = Path(__file__).parent / 'db.sqlite3'
    
    if not sqlite_path.exists():
        print("SQLite file not found")
        return
    
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Tables in SQLite database:")
    for table in tables:
        table_name = table[0]
        print(f"- {table_name}")
        
        # Count rows in each table
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
            
            # Show sample data for important tables
            if table_name in ['auth_user', 'universities_university'] and count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print(f"  Sample data: {rows}")
        except Exception as e:
            print(f"  Error reading table: {e}")
    
    conn.close()

if __name__ == "__main__":
    inspect_sqlite()