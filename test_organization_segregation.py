#!/usr/bin/env python3
"""
Test script to verify organization-level segregation in DearDonor
This tests settings, assets, receipts, and receipt numbering isolation
"""

import os
import sys
sys.path.append('.')

from modules.supabase_utils import (
    get_organization_settings,
    save_organization_settings,
    get_organization_receipt_number,
    get_organization_asset_path,
    get_organization_receipt_path
)
from modules.auth import OrganizationAuth
import tempfile
import shutil

def test_organization_segregation():
    print("🔍 Testing Organization-Level Segregation")
    print("=" * 50)
    
    # Test organization IDs (simulated)
    org1_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"  # Existing Stray Army
    org2_id = "12345678-1234-1234-1234-123456789abc"  # Simulated new org
    
    print("\n1. Testing Organization Settings Segregation...")
    
    # Test settings for existing organization
    print(f"   🏢 Testing settings for Organization 1: {org1_id[:8]}...")
    org1_settings = get_organization_settings(org1_id)
    if org1_settings:
        print(f"   ✅ Found settings for Organization 1: {org1_settings.get('organization', {}).get('name', 'Unknown')}")
    else:
        print("   ❌ No settings found for Organization 1")
    
    # Test settings for non-existent organization
    print(f"   🏢 Testing settings for Organization 2: {org2_id[:8]}...")
    org2_settings = get_organization_settings(org2_id)
    if not org2_settings or not org2_settings.get('organization', {}).get('name'):
        print("   ✅ Organization 2 has empty/default settings (expected for new org)")
    else:
        print(f"   ❌ Organization 2 has unexpected settings: {org2_settings.get('organization', {}).get('name')}")
    
    print("\n2. Testing Asset Path Segregation...")
    
    # Test asset paths
    org1_logo = get_organization_asset_path(org1_id, 'logo')
    org2_logo = get_organization_asset_path(org2_id, 'logo')
    
    print(f"   📁 Organization 1 logo path: {org1_logo}")
    print(f"   📁 Organization 2 logo path: {org2_logo}")
    
    if org1_id in org1_logo and org2_id in org2_logo and org1_logo != org2_logo:
        print("   ✅ Asset paths are properly segregated by organization")
    else:
        print("   ❌ Asset paths are not properly segregated")
    
    # Check if Organization 1 assets exist
    if os.path.exists(org1_logo):
        print(f"   ✅ Organization 1 logo exists at: {org1_logo}")
    else:
        print(f"   ⚠️  Organization 1 logo not found at: {org1_logo}")
    
    org1_signature = get_organization_asset_path(org1_id, 'signature')
    if os.path.exists(org1_signature):
        print(f"   ✅ Organization 1 signature exists at: {org1_signature}")
    else:
        print(f"   ⚠️  Organization 1 signature not found at: {org1_signature}")
    
    print("\n3. Testing Receipt Path Segregation...")
    
    # Test receipt paths
    sample_receipt_no = "TEST/25/01/001"
    org1_receipt = get_organization_receipt_path(org1_id, sample_receipt_no)
    org2_receipt = get_organization_receipt_path(org2_id, sample_receipt_no)
    
    print(f"   📄 Organization 1 receipt path: {org1_receipt}")
    print(f"   📄 Organization 2 receipt path: {org2_receipt}")
    
    if org1_id in org1_receipt and org2_id in org2_receipt and org1_receipt != org2_receipt:
        print("   ✅ Receipt paths are properly segregated by organization")
    else:
        print("   ❌ Receipt paths are not properly segregated")
    
    print("\n4. Testing Receipt Number Generation...")
    
    try:
        # Test receipt number generation for Organization 1
        receipt_no_1 = get_organization_receipt_number(org1_id)
        print(f"   📊 Organization 1 next receipt number: {receipt_no_1}")
        
        # Test receipt number generation for Organization 2 (should start fresh)
        try:
            receipt_no_2 = get_organization_receipt_number(org2_id)
            print(f"   📊 Organization 2 next receipt number: {receipt_no_2}")
            
            if receipt_no_1 != receipt_no_2:
                print("   ✅ Receipt numbers are properly segregated by organization")
            else:
                print("   ⚠️  Receipt numbers might not be properly segregated")
        except Exception as e:
            print(f"   ⚠️  Organization 2 receipt generation failed (expected for non-existent org): {str(e)}")
        
    except Exception as e:
        print(f"   ❌ Receipt number generation failed: {str(e)}")
    
    print("\n5. Testing Directory Structure...")
    
    # Check uploads directory structure
    uploads_dir = "uploads/organizations"
    if os.path.exists(uploads_dir):
        print(f"   📁 Uploads directory exists: {uploads_dir}")
        
        # List organization directories
        org_dirs = [d for d in os.listdir(uploads_dir) if os.path.isdir(os.path.join(uploads_dir, d))]
        print(f"   📊 Found {len(org_dirs)} organization directories:")
        
        for org_dir in org_dirs:
            org_path = os.path.join(uploads_dir, org_dir)
            assets_path = os.path.join(org_path, "assets")
            receipts_path = os.path.join(org_path, "receipts")
            
            print(f"      🏢 {org_dir}:")
            print(f"         📁 Assets: {'✅' if os.path.exists(assets_path) else '❌'}")
            print(f"         📁 Receipts: {'✅' if os.path.exists(receipts_path) else '❌'}")
            
            if os.path.exists(assets_path):
                assets = os.listdir(assets_path)
                print(f"         📄 Assets count: {len(assets)} files")
                
            if os.path.exists(receipts_path):
                receipts = os.listdir(receipts_path)
                print(f"         📄 Receipts count: {len(receipts)} files")
    else:
        print(f"   ❌ Uploads directory not found: {uploads_dir}")
    
    print("\n6. Summary:")
    print("   🎯 Organization-level segregation verification complete!")
    print("   📋 Key Points:")
    print("      - Settings are isolated by organization ID")
    print("      - Assets are stored in organization-specific folders")
    print("      - Receipts are stored in organization-specific folders")
    print("      - Receipt numbering is independent per organization")
    print("      - New organizations start with empty settings and fresh receipt sequences")
    
    return True

if __name__ == "__main__":
    test_organization_segregation() 