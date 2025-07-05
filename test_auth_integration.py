#!/usr/bin/env python3
"""
Test script to verify authentication integration
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.auth import OrganizationAuth

def test_auth_integration():
    """Test authentication integration"""
    print("🔍 Testing Authentication Integration")
    print("=" * 50)
    
    auth = OrganizationAuth()
    
    # Test 1: Check if authentication methods work
    print("\n1. Testing authentication methods...")
    
    try:
        # Test login
        success, message, org_data = auth.login("thestrayarmy@gmail.com", "Shiro@123")
        if success:
            print("✅ Login method works")
            print(f"   Organization: {org_data['name']}")
            print(f"   Email: {org_data['email']}")
            print(f"   Slug: {org_data['slug']}")
        else:
            print(f"❌ Login failed: {message}")
            
        # Test authentication check
        is_auth = auth.is_authenticated()
        print(f"✅ Authentication check: {is_auth}")
        
        # Test get current organization
        current_org = auth.get_current_organization()
        if current_org:
            print("✅ Get current organization works")
            print(f"   Current org: {current_org['name']}")
        else:
            print("❌ Get current organization failed")
            
    except Exception as e:
        print(f"❌ Authentication methods failed: {e}")
    
    # Test 2: Test logout
    print("\n2. Testing logout...")
    try:
        auth.logout()
        is_auth_after_logout = auth.is_authenticated()
        print(f"✅ Logout successful. Authenticated: {is_auth_after_logout}")
    except Exception as e:
        print(f"❌ Logout failed: {e}")
    
    print("\n🎉 Authentication integration test completed!")

if __name__ == "__main__":
    test_auth_integration() 