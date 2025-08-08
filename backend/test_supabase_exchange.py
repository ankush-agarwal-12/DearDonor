#!/usr/bin/env python3
"""
Test script for Supabase JWT exchange endpoint
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") 
BACKEND_URL = "http://localhost:8000"

def get_supabase_jwt(email: str, password: str):
    """Get a Supabase JWT by signing in"""
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ Supabase sign in failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_exchange_endpoint(supabase_jwt: str):
    """Test the /auth/exchange endpoint"""
    url = f"{BACKEND_URL}/auth/exchange"
    headers = {"Content-Type": "application/json"}
    data = {"supabase_token": supabase_jwt}
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Exchange endpoint status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_backend_api(backend_jwt: str):
    """Test using the backend JWT on a protected endpoint"""
    url = f"{BACKEND_URL}/auth/me"
    headers = {"Authorization": f"Bearer {backend_jwt}"}
    
    response = requests.get(url, headers=headers)
    print(f"Backend API test status: {response.status_code}")
    print(f"Response: {response.text}")

def main():
    print("🔐 Testing Supabase JWT Exchange Flow")
    print("=" * 50)
    
    # You need to replace these with actual Supabase Auth user credentials
    # (Not your organization table credentials!)
    email = input("Enter Supabase Auth email: ").strip()
    password = input("Enter Supabase Auth password: ").strip()
    
    print("\n1. Getting Supabase JWT...")
    supabase_jwt = get_supabase_jwt(email, password)
    
    if not supabase_jwt:
        print("❌ Failed to get Supabase JWT")
        return
    
    print(f"✅ Got Supabase JWT: {supabase_jwt[:50]}...")
    
    print("\n2. Testing exchange endpoint...")
    backend_jwt = test_exchange_endpoint(supabase_jwt)
    
    if not backend_jwt:
        print("❌ Failed to exchange token")
        return
    
    print(f"✅ Got backend JWT: {backend_jwt[:50]}...")
    
    print("\n3. Testing backend API with new JWT...")
    test_backend_api(backend_jwt)
    
    print("\n🎉 Test complete!")

if __name__ == "__main__":
    main() 