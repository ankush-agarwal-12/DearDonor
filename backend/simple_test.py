#!/usr/bin/env python3
"""
Simple test to verify JWT secret works
"""

import os
import jwt
from dotenv import load_dotenv

load_dotenv()

# Your updated token (with full payload)
token = "eyJhbGciOiJIUzI1NiIsImtpZCI6IkpKWkJHMUtHVFYwTkxXMmYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3d3cXRrcXZjbW1jY2Vza3N0bnlmLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiMWI0YzJlNy02NzAxLTQzZTItYWQ4Yy00NTM5MGE1YzMzNTEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU0NjM0MTE0LCJpYXQiOjE3NTQ2MzA1MTQsImVtYWlsIjoiYW5rdXNoMUBuZ28ub3JnIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTQ2MzA1MTR9XSwic2Vzc2lvbl9pZCI6Ijk1NDBiMWI3LWU3MjYtNDIyNi04OWVkLWQ4NmExMzkxYWU1YSIsImlzX2Fub255bW91cyI6ZmFsc2V9.JW1rKyT0MndjHQ72AJt0QyBejTiQaA3s5lzVq5jXpWk"

def test_jwt_verification():
    """Test different JWT secrets to find the right one"""
    
    print("🔐 Testing JWT Verification")
    print("=" * 40)
    
    # Get env variables
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY") 
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Service Key: {service_key[:10]}..." if service_key else "Service Key: Not set")
    print(f"Anon Key: {anon_key[:10]}..." if anon_key else "Anon Key: Not set")
    print(f"JWT Secret: {jwt_secret[:10]}..." if jwt_secret else "JWT Secret: Not set")
    
    # Try different keys
    keys_to_try = [
        ("JWT_SECRET", jwt_secret),
        ("SERVICE_KEY", service_key),
        ("ANON_KEY", anon_key)
    ]
    
    for key_name, key_value in keys_to_try:
        if not key_value:
            print(f"\n❌ {key_name}: Not available")
            continue
            
        print(f"\n🔑 Testing with {key_name}...")
        try:
            # Try to decode with minimal validation first
            claims = jwt.decode(
                token,
                key_value,
                algorithms=["HS256"],
                options={"verify_signature": True, "verify_exp": False, "verify_iss": False}
            )
            
            print(f"✅ SUCCESS with {key_name}!")
            print(f"   User ID: {claims.get('sub')}")
            print(f"   Email: {claims.get('email')}")
            print(f"   Issued at: {claims.get('iat')}")
            return key_name, key_value
            
        except Exception as e:
            print(f"❌ Failed with {key_name}: {str(e)}")
    
    print("\n😞 None of the keys worked. You need to find the correct JWT secret from Supabase dashboard.")
    return None, None

if __name__ == "__main__":
    test_jwt_verification() 