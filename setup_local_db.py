#!/usr/bin/env python3
"""
Script to set up local PostgreSQL database for development.
"""
import subprocess
import sys

def run_command(cmd, description, ignore_error=False):
    """Run a shell command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"SUCCESS: {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_error:
            print(f"WARNING: {description} failed (ignoring): {e.stderr}")
            return False
        else:
            print(f"ERROR in {description}: {e.stderr}")
            sys.exit(1)

def main():
    print("Setting up local PostgreSQL database...")
    
    # Create the database (ignore error if it already exists)
    create_cmd = 'createdb -h localhost -p 5432 -U postgres addistemari'
    run_command(create_cmd, "Creating addistemari database", ignore_error=True)
    
    # Run Django migrations
    migrate_cmd = 'python manage.py migrate'
    run_command(migrate_cmd, "Running Django migrations")
    
    # Create groups
    groups_cmd = 'python manage.py create_groups'
    run_command(groups_cmd, "Creating default groups")
    
    print("Local database setup completed!")
    print("You can now run: python manage.py runserver")

if __name__ == "__main__":
    main()