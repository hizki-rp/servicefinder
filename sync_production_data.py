#!/usr/bin/env python3
"""
Script to sync production data to local development database.
This creates a sanitized copy of production data for local development.
"""
import os
import subprocess
import sys
from datetime import datetime

# Production database URL
PROD_DB_URL = "postgresql://addist_user:Sg0hMPlix46LhLADS2CHq7m9on8nf52c@dpg-d3e1lap5pdvs73fr8js0-a.oregon-postgres.render.com/addist"

# Local database settings
LOCAL_DB_HOST = "localhost"
LOCAL_DB_PORT = "5432"
LOCAL_DB_NAME = "addistemari"
LOCAL_DB_USER = "postgres"
LOCAL_DB_PASSWORD = "root25"

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e.stderr}")
        sys.exit(1)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = f"production_dump_{timestamp}.sql"
    
    print("🔄 Starting production data sync...")
    
    # 1. Create dump from production
    dump_cmd = f'pg_dump "{PROD_DB_URL}" > {dump_file}'
    run_command(dump_cmd, "Creating production database dump")
    
    # 2. Drop and recreate local database
    drop_cmd = f'dropdb -h {LOCAL_DB_HOST} -p {LOCAL_DB_PORT} -U {LOCAL_DB_USER} {LOCAL_DB_NAME}'
    create_cmd = f'createdb -h {LOCAL_DB_HOST} -p {LOCAL_DB_PORT} -U {LOCAL_DB_USER} {LOCAL_DB_NAME}'
    
    print("⚠️  Dropping local database...")
    subprocess.run(drop_cmd, shell=True)  # Don't fail if DB doesn't exist
    
    run_command(create_cmd, "Creating fresh local database")
    
    # 3. Import dump to local database
    import_cmd = f'psql -h {LOCAL_DB_HOST} -p {LOCAL_DB_PORT} -U {LOCAL_DB_USER} -d {LOCAL_DB_NAME} -f {dump_file}'
    run_command(import_cmd, "Importing production data to local database")
    
    # 4. Clean up dump file
    os.remove(dump_file)
    print(f"🗑️  Cleaned up dump file: {dump_file}")
    
    print("✅ Production data sync completed successfully!")
    print("💡 Your local database now has the latest production data.")
    print("⚠️  Remember: This is real user data - handle with care!")

if __name__ == "__main__":
    main()