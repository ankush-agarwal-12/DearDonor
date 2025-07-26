#!/usr/bin/env python3
"""
Reset Password Script for DearDonor
This script allows you to set a new password for the organization
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

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def reset_password():
    """Reset password for organization"""
    print("🔐 Reset Password for DearDonor Organization")
    print("=" * 50)
    
    try:
        # Get current organization
        result = supabase.table('organizations').select('*').execute()
        
        if not result.data:
            print("❌ No organization found in database!")
            return
        
        org = result.data[0]
        print(f"Organization: {org['name']}")
        print(f"Email: {org['email']}")
        print()
        
        # Get new password
        new_password = getpass.getpass("Enter new password: ")
        confirm_password = getpass.getpass("Confirm new password: ")
        
        if new_password != confirm_password:
            print("❌ Passwords don't match!")
            return
        
        if len(new_password) < 6:
            print("❌ Password must be at least 6 characters long!")
            return
        
        # Hash the password
        hashed_password = hash_password(new_password)
        
        # Update in database
        update_result = supabase.table('organizations').update({
            'password_hash': hashed_password
        }).eq('id', org['id']).execute()
        
        if update_result.data:
            print("✅ Password updated successfully!")
            print(f"New password hash: {hashed_password[:50]}...")
            print("\nYou can now login with the new password.")
        else:
            print("❌ Failed to update password in database")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    reset_password() 