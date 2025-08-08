#!/usr/bin/env python3
"""
Test organization mapping logic without JWT verification
"""

import sys
import os
sys.path.append('backend')

from backend.app.db.session import get_db
from backend.app.models.organization import Organization

def test_organization_lookup():
    """Test if we can find the organization by auth_user_id and email"""
    
    # Test data from your JWT
    supabase_user_id = "b1b4c2e7-6701-43e2-ad8c-45390a5c3351"
    supabase_email = "ankush1@ngo.org"
    
    print("🔍 Testing Organization Lookup")
    print("=" * 40)
    print(f"Supabase User ID: {supabase_user_id}")
    print(f"Supabase Email: {supabase_email}")
    
    # Get database session
    db = next(get_db())
    
    print("\n1. Testing lookup by auth_user_id...")
    try:
        # Check if Organization has auth_user_id column
        if hasattr(Organization, "auth_user_id"):
            org_by_id = db.query(Organization).filter(
                getattr(Organization, "auth_user_id") == supabase_user_id
            ).first()
            
            if org_by_id:
                print(f"✅ Found organization by auth_user_id: {org_by_id.name}")
                print(f"   Org ID: {org_by_id.id}")
                print(f"   Email: {org_by_id.email}")
                print(f"   Slug: {org_by_id.slug}")
            else:
                print("❌ No organization found by auth_user_id")
        else:
            print("❌ Organization model doesn't have auth_user_id column")
    except Exception as e:
        print(f"❌ Error looking up by auth_user_id: {e}")
    
    print("\n2. Testing lookup by email...")
    try:
        org_by_email = db.query(Organization).filter(
            Organization.email == supabase_email
        ).first()
        
        if org_by_email:
            print(f"✅ Found organization by email: {org_by_email.name}")
            print(f"   Org ID: {org_by_email.id}")
            print(f"   Has auth_user_id: {hasattr(org_by_email, 'auth_user_id')}")
            if hasattr(org_by_email, 'auth_user_id'):
                print(f"   Auth User ID: {getattr(org_by_email, 'auth_user_id', 'N/A')}")
        else:
            print("❌ No organization found by email")
    except Exception as e:
        print(f"❌ Error looking up by email: {e}")
    
    print("\n🎉 Test complete!")
    db.close()

if __name__ == "__main__":
    test_organization_lookup() 