"""
Script to help setup local PostgreSQL to match production
Run this after installing PostgreSQL locally
"""
import os
import subprocess
import sys

def setup_local_postgres():
    """Setup local PostgreSQL database"""
    
    db_name = "uni_finder_local"
    
    print("🔧 Setting up local PostgreSQL database...")
    
    try:
        # Create database
        print(f"Creating database: {db_name}")
        subprocess.run(['createdb', db_name], check=True)
        print("✅ Database created successfully")
        
        # Update .env file
        env_content = f"""
# Local PostgreSQL Database
DATABASE_URL=postgresql://localhost/{db_name}

# Keep existing settings
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

# Your existing Chapa keys
CHAPA_SECRET_KEY="CHAPUBK_TEST-MSqxqLqYEsiV06OnQjolrfc72tltyjYg"
CHAPA_WEBHOOK_SECRET="95f7c4e2d8c42ff3052e5ad4a57a8d767b5843c9af8726a31cdb57a46e002b33"
"""
        
        with open('.env', 'w') as f:
            f.write(env_content.strip())
        
        print("✅ .env file updated with PostgreSQL settings")
        
        print("\n📋 Next steps:")
        print("1. Get production database dump from Render")
        print("2. Import: psql -d uni_finder_local < production_backup.sql")
        print("3. Run: python manage.py migrate")
        print("4. Test your new features with real production data")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print("Make sure PostgreSQL is installed and running")
        sys.exit(1)

if __name__ == '__main__':
    setup_local_postgres()