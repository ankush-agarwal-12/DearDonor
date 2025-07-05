# test_auth.py
from modules.auth import OrganizationAuth

def test_authentication():
    auth = OrganizationAuth()
    
    print("🔐 Testing Authentication System")
    print("=" * 50)
    
    # Test 1: Login with your existing organization
    print("\n1. Testing login with The Stray Army...")
    success, message, org_data = auth.login("thestrayarmy@gmail.com", "Shiro.123")
    
    if success:
        print(f"✅ Login successful!")
        print(f"   Organization: {org_data['name']}")
        print(f"   ID: {org_data['id']}")
        print(f"   Slug: {org_data['slug']}")
        stray_army_id = org_data['id']
    else:
        print(f"❌ Login failed: {message}")
        return
    
    # Test 2: Test wrong password
    print("\n2. Testing wrong password...")
    success, message, _ = auth.login("thestrayarmy@gmail.com", "wrongpassword")
    if not success:
        print(f"✅ Correctly rejected wrong password: {message}")
    else:
        print(f"❌ Should have rejected wrong password!")
    
    # Test 3: Test password change
    print("\n3. Testing password change...")
    success, message = auth.change_password(stray_army_id, "Shiro.123", "Shiro@123")
    
    if success:
        print(f"✅ Password changed: {message}")
        
        # Test login with new password
        print("\n4. Testing login with new password...")
        success, message, org_data = auth.login("thestrayarmy@gmail.com", "Shiro@123")
        if success:
            print(f"✅ Login with new password successful!")
        else:
            print(f"❌ Login with new password failed: {message}")
    else:
        print(f"❌ Password change failed: {message}")
    
    # Test 5: Test registration (new org)
    print("\n5. Testing new organization registration...")
    success, message, org_data = auth.register(
        name="Test Animal Shelter",
        email="test@animalshelter.com", 
        password="TestPassword123!",
        phone="+91 9876543210",
        website="www.testanimalshelter.com"
    )
    
    if success:
        print(f"✅ Registration successful!")
        print(f"   Organization: {org_data['name']}")
        print(f"   Email: {org_data['email']}")
        print(f"   Slug: {org_data['slug']}")
        
        # Test login with new org
        success, message, org_data = auth.login("test@animalshelter.com", "TestPassword123!")
        if success:
            print(f"✅ New organization can login successfully!")
        else:
            print(f"❌ New organization login failed: {message}")
    else:
        print(f"❌ Registration failed: {message}")
    
    print("\n🎉 Authentication testing complete!")

if __name__ == "__main__":
    test_authentication()