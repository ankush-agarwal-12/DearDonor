# password_helper.py
from modules.auth import OrganizationAuth
import getpass

def change_stray_army_password():
    auth = OrganizationAuth()
    
    print("🔐 Change Password for The Stray Army")
    print("=" * 40)
    
    # Get organization ID
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    
    result = supabase.table("organizations")\
        .select("id")\
        .eq("email", "thestrayarmy@gmail.com")\
        .execute()
    
    if not result.data:
        print("❌ The Stray Army organization not found!")
        return
    
    org_id = result.data[0]['id']
    
    print("Current password is: changeme123")
    current_password = input("Enter current password: ")
    
    while True:
        new_password = getpass.getpass("Enter new password: ")
        confirm_password = getpass.getpass("Confirm new password: ")
        
        if new_password != confirm_password:
            print("❌ Passwords don't match. Try again.")
            continue
        
        # Validate password
        is_valid, message = auth.validate_password(new_password)
        if not is_valid:
            print(f"❌ {message}")
            continue
        
        break
    
    # Change password
    success, message = auth.change_password(org_id, current_password, new_password)
    
    if success:
        print(f"✅ {message}")
        print("You can now login with your new password!")
    else:
        print(f"❌ {message}")

if __name__ == "__main__":
    change_stray_army_password()