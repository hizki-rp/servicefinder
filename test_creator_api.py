#!/usr/bin/env python
import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_api.settings')
django.setup()

# Test the API endpoints
BASE_URL = 'http://127.0.0.1:8000/api'

def test_settings_endpoint():
    """Test the settings endpoint"""
    try:
        response = requests.get(f'{BASE_URL}/creator/settings/')
        print(f"Settings endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Settings data: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing settings endpoint: {e}")

def test_posts_endpoint():
    """Test the posts endpoint"""
    try:
        response = requests.get(f'{BASE_URL}/creator/posts/')
        print(f"Posts endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Posts data: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing posts endpoint: {e}")

if __name__ == '__main__':
    print("Testing Creator API endpoints...")
    print("Make sure Django server is running on port 8000")
    print("-" * 50)
    test_settings_endpoint()
    print("-" * 50)
    test_posts_endpoint()