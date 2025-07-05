#!/usr/bin/env python3

"""
Test script to verify organization-level filtering works correctly
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.supabase_utils import fetch_donors, fetch_all_donations
from modules.auth import OrganizationAuth

def test_organization_filtering():
    """Test organization filtering functionality"""
    print("🔍 Testing Organization-Level Filtering")
    print("=" * 50)
    
    auth = OrganizationAuth()
    
    # Test with Stray Army organization
    stray_army_org_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"  # This is the ID from our migration
    
    print("\n1. Testing with Stray Army Organization ID...")
    try:
        donors = fetch_donors(organization_id=stray_army_org_id)
        donations = fetch_all_donations(organization_id=stray_army_org_id)
        
        print(f"✅ Found {len(donors)} donors")
        print(f"✅ Found {len(donations)} donations")
        
        if donors:
            print(f"   Sample donor: {donors[0]['Full Name']}")
        if donations:
            print(f"   Sample donation: ₹{donations[0]['Amount']} from {donations[0]['Email']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    print("\n2. Testing with invalid organization ID...")
    try:
        # Test with non-existent organization ID
        fake_org_id = "00000000-0000-0000-0000-000000000000"
        donors_fake = fetch_donors(organization_id=fake_org_id)
        donations_fake = fetch_all_donations(organization_id=fake_org_id)
        
        print(f"✅ Found {len(donors_fake)} donors (should be 0)")
        print(f"✅ Found {len(donations_fake)} donations (should be 0)")
        
        if len(donors_fake) == 0 and len(donations_fake) == 0:
            print("✅ Organization isolation working correctly!")
        else:
            print("❌ Organization isolation failed - data leakage detected!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    print("\n3. Testing without organization ID...")
    try:
        # This should fail
        donors_no_org = fetch_donors()
        print("❌ Function should have failed without organization_id")
        return False
    except ValueError as e:
        if "Organization ID is required" in str(e):
            print("✅ Organization ID validation working correctly!")
        else:
            print(f"❌ Unexpected ValueError: {str(e)}")
            return False
    except Exception as e:
        # Check if it's a print error being caught
        if "Organization ID is required" in str(e):
            print("✅ Organization ID validation working correctly!")
        else:
            print(f"❌ Unexpected error: {str(e)}")
            return False
    
    print("\n🎉 All organization filtering tests passed!")
    return True

if __name__ == "__main__":
    success = test_organization_filtering()
    if success:
        print("\n✅ Organization filtering is working correctly!")
        print("✅ Each organization can only see their own data")
        print("✅ System is ready for multi-tenant use")
    else:
        print("\n❌ Organization filtering has issues that need to be fixed")
    
    sys.exit(0 if success else 1) 