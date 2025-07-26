#!/usr/bin/env python3
"""
Test Login Script for DearDonor
This script tests the login functionality
"""

import bcrypt
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import getpass

# Load environment variables
load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def test_login():
    """Test login functionality"""
    print("🔐 Test Login for DearDonor")
    print("=" * 30)
    
    try:
        # Get organization
        result = supabase.table('organizations').select('*').execute()
        
        if not result.data:
            print("❌ No organization found!")
            return
        
        org = result.data[0]
        print(f"Organization: {org['name']}")
        print(f"Email: {org['email']}")
        print()
        
        # Test login
        email = input("Enter email: ").strip()
        password = getpass.getpass("Enter password: ")
        
        if email != org['email']:
            print("❌ Invalid email!")
            return
        
        if verify_password(password, org['password_hash']):
            print("✅ Login successful!")
            print(f"Welcome, {org['name']}!")
            print(f"Phone: {org.get('phone', 'Not set')}")
            print(f"Website: {org.get('website', 'Not set')}")
        else:
            print("❌ Invalid password!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_login() 