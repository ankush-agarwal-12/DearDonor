# verify_migration.py
import json
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def verify_migration():
    print("🔍 Verifying Migration for The Stray Army...")
    
    # Check organization
    org_result = supabase.table("organizations").select("*").eq("name", "The Stray Army Charitable Organisation").execute()
    if org_result.data:
        org = org_result.data[0]
        print(f"✅ Organization found: {org['name']}")
        print(f"   📧 Email: {org['email']}")
        print(f"   🏢 Address: {org['office_address']}")
        org_id = org['id']
    else:
        print("❌ Organization not found!")
        return
    
    # Check donors count
    donors_result = supabase.table("donors").select("id").eq("organization_id", org_id).execute()
    print(f"👥 Donors migrated: {len(donors_result.data)}")
    
    # Check donations count  
    donations_result = supabase.table("donations").select("id").eq("organization_id", org_id).execute()
    print(f"💰 Donations migrated: {len(donations_result.data)}")
    
    # Check settings
    settings_result = supabase.table("organization_settings").select("*").eq("organization_id", org_id).execute()
    print(f"⚙️ Settings migrated: {len(settings_result.data)}")
    
    for setting in settings_result.data:
        print(f"   - {setting['setting_key']}: {setting['setting_value']}")
    
    # Check donation purposes
    purposes_setting = next((s for s in settings_result.data if s['setting_key'] == 'donation_purposes'), None)
    if purposes_setting:
        purposes = purposes_setting['setting_value']
        print(f"🎯 Donation purposes: {purposes}")
    
    print("\n🎉 Migration verification complete!")

if __name__ == "__main__":
    verify_migration()