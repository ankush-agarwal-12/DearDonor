# modules/auth.py
import streamlit as st
import bcrypt
import re
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

class OrganizationAuth:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        return True, "Password is valid"
    
    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-friendly slug from organization name"""
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        slug = re.sub(r'[^a-z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug)
        return slug[:50]  # Limit length
    
    def login(self, email: str, password: str) -> tuple[bool, str, dict]:
        """Login organization"""
        try:
            if not self.validate_email(email):
                return False, "Invalid email format", {}
            
            # Get organization by email
            result = supabase.table("organizations")\
                .select("*")\
                .eq("email", email.lower())\
                .eq("status", "active")\
                .execute()
            
            if not result.data:
                return False, "Organization not found or inactive", {}
            
            org = result.data[0]
            
            # Verify password
            if not self.verify_password(password, org['password_hash']):
                return False, "Invalid password", {}
            
            # Update last login
            supabase.table("organizations")\
                .update({"last_login": datetime.now().isoformat()})\
                .eq("id", org['id'])\
                .execute()
            
            # Return organization data (without password hash)
            org_data = {
                'id': org['id'],
                'name': org['name'],
                'email': org['email'],
                'slug': org['slug'],
                'phone': org['phone'],
                'website': org['website']
            }
            
            return True, "Login successful", org_data
            
        except Exception as e:
            return False, f"Login error: {str(e)}", {}
    
    def register(self, name: str, email: str, password: str, phone: str = None, website: str = None) -> tuple[bool, str, dict]:
        """Register new organization"""
        try:
            # Validate inputs
            if not name or len(name.strip()) < 2:
                return False, "Organization name must be at least 2 characters", {}
            
            if not self.validate_email(email):
                return False, "Invalid email format", {}
            
            is_valid_pwd, pwd_msg = self.validate_password(password)
            if not is_valid_pwd:
                return False, pwd_msg, {}
            
            # Check if email already exists
            existing = supabase.table("organizations")\
                .select("id")\
                .eq("email", email.lower())\
                .execute()
            
            if existing.data:
                return False, "Email already registered", {}
            
            # Generate slug
            base_slug = self.generate_slug(name)
            slug = base_slug
            counter = 1
            
            # Ensure unique slug
            while True:
                slug_check = supabase.table("organizations")\
                    .select("id")\
                    .eq("slug", slug)\
                    .execute()
                
                if not slug_check.data:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create organization
            org_data = {
                'name': name.strip(),
                'email': email.lower(),
                'password_hash': password_hash,
                'slug': slug,
                'phone': phone,
                'website': website,
                'status': 'active',
                'email_verified': False
            }
            
            result = supabase.table("organizations").insert(org_data).execute()
            
            if result.data:
                org = result.data[0]
                
                # Create default settings for new organization
                self._create_default_settings(org['id'])
                
                org_response = {
                    'id': org['id'],
                    'name': org['name'],
                    'email': org['email'],
                    'slug': org['slug']
                }
                
                return True, "Organization registered successfully", org_response
            else:
                return False, "Failed to create organization", {}
                
        except Exception as e:
            return False, f"Registration error: {str(e)}", {}
    
    def _create_default_settings(self, org_id: str):
        """Create default settings for new organization"""
        default_settings = [
            {
                'organization_id': org_id,
                'setting_key': 'donation_purposes',
                'setting_value': ['General Fund', 'Corpus Fund', 'Emergency Fund']
            },
            {
                'organization_id': org_id,
                'setting_key': 'payment_methods', 
                'setting_value': ['Cash', 'UPI', 'Bank Transfer', 'Cheque']
            },
            {
                'organization_id': org_id,
                'setting_key': 'receipt_format',
                'setting_value': {
                    'prefix': 'REC',
                    'format': '{prefix}/{YY}/{MM}/{XXX}',
                    'next_sequence': 1
                }
            }
        ]
        
        for setting in default_settings:
            supabase.table("organization_settings").insert(setting).execute()
    
    def change_password(self, org_id: str, current_password: str, new_password: str) -> tuple[bool, str]:
        """Change organization password"""
        try:
            # Get current organization
            result = supabase.table("organizations")\
                .select("password_hash")\
                .eq("id", org_id)\
                .execute()
            
            if not result.data:
                return False, "Organization not found"
            
            org = result.data[0]
            
            # Verify current password
            if not self.verify_password(current_password, org['password_hash']):
                return False, "Current password is incorrect"
            
            # Validate new password
            is_valid, message = self.validate_password(new_password)
            if not is_valid:
                return False, message
            
            # Hash new password
            new_hash = self.hash_password(new_password)
            
            # Update password
            supabase.table("organizations")\
                .update({"password_hash": new_hash, "updated_at": datetime.now().isoformat()})\
                .eq("id", org_id)\
                .execute()
            
            return True, "Password changed successfully"
            
        except Exception as e:
            return False, f"Password change error: {str(e)}"
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return 'organization' in st.session_state and st.session_state.organization is not None
    
    @staticmethod
    def get_current_organization() -> dict:
        """Get current organization from session"""
        return st.session_state.get('organization', {})
    
    @staticmethod
    def logout():
        """Clear session"""
        if 'organization' in st.session_state:
            del st.session_state.organization
        # Clear other session state as needed
        for key in list(st.session_state.keys()):
            if key.startswith('org_'):
                del st.session_state[key]