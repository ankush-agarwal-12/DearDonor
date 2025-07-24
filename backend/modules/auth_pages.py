# modules/auth_pages.py
import streamlit as st
from modules.auth import OrganizationAuth

def show_login_page():
    """Show login form"""
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 2rem 0;">
                <h1>🎗️ DearDonor</h1>
                <h3>Nonprofit Management System</h3>
                <p>Sign in to your organization account</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            
            email = st.text_input(
                "Organization Email",
                placeholder="your-org@example.com",
                help="Email address used during registration"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                help="Your organization password"
            )
            
            remember_me = st.checkbox("Remember me")
            
            login_clicked = st.form_submit_button(
                "🔑 Login",
                use_container_width=True,
                type="primary"
            )
            
            if login_clicked:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    auth = OrganizationAuth()
                    success, message, org_data = auth.login(email, password)
                    
                    if success:
                        # Set session state
                        st.session_state.organization = org_data
                        st.success(f"✅ Welcome back, {org_data['name']}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # Links
        st.markdown("---")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📝 Register New Organization", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        
        with col_b:
            if st.button("🔄 Forgot Password?", use_container_width=True):
                st.info("Please contact support for password reset")

def show_register_page():
    """Show registration form"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 2rem 0;">
                <h1>🎗️ DearDonor</h1>
                <h3>Register Your Organization</h3>
                <p>Create a new account for your nonprofit</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Registration form
        with st.form("register_form"):
            st.markdown("### 📝 Organization Details")
            
            org_name = st.text_input(
                "Organization Name *",
                placeholder="Your Nonprofit Organization",
                help="Full legal name of your organization"
            )
            
            email = st.text_input(
                "Email Address *",
                placeholder="contact@yourorg.com",
                help="This will be your login email"
            )
            
            col_pwd1, col_pwd2 = st.columns(2)
            with col_pwd1:
                password = st.text_input(
                    "Password *",
                    type="password",
                    help="Must be at least 8 characters with uppercase, lowercase, and number"
                )
            
            with col_pwd2:
                confirm_password = st.text_input(
                    "Confirm Password *",
                    type="password"
                )
            
            col_phone, col_website = st.columns(2)
            with col_phone:
                phone = st.text_input(
                    "Phone Number",
                    placeholder="+91 9876543210"
                )
            
            with col_website:
                website = st.text_input(
                    "Website",
                    placeholder="www.yourorg.com"
                )
            
            # Terms and conditions
            agree_terms = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy *",
                help="You must agree to continue"
            )
            
            register_clicked = st.form_submit_button(
                "🚀 Create Organization",
                use_container_width=True,
                type="primary"
            )
            
            if register_clicked:
                # Validate form
                if not org_name or not email or not password:
                    st.error("Please fill in all required fields marked with *")
                elif password != confirm_password:
                    st.error("Passwords don't match")
                elif not agree_terms:
                    st.error("Please agree to the Terms of Service")
                else:
                    auth = OrganizationAuth()
                    success, message, org_data = auth.register(
                        name=org_name,
                        email=email,
                        password=password,
                        phone=phone,
                        website=website
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info(f"Your organization slug: **{org_data['slug']}**")
                        st.balloons()
                        
                        # Auto-login after registration
                        st.session_state.organization = org_data
                        st.session_state.show_register = False
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # Back to login
        st.markdown("---")
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.show_register = False
            st.rerun()

def show_auth_wrapper():
    """Main authentication wrapper"""
    
    # Initialize session state
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    # Show appropriate page
    if st.session_state.show_register:
        show_register_page()
    else:
        show_login_page()

def show_profile_settings():
    """Show profile and password change"""
    auth = OrganizationAuth()
    org = auth.get_current_organization()
    
    st.markdown("### 👤 Organization Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Organization:** {org['name']}")
        st.info(f"**Email:** {org['email']}")
        st.info(f"**Slug:** {org['slug']}")
    
    with col2:
        if org.get('phone'):
            st.info(f"**Phone:** {org['phone']}")
        if org.get('website'):
            st.info(f"**Website:** {org['website']}")
    
    st.markdown("---")
    
    # Password change section
    st.markdown("### 🔐 Change Password")
    
    with st.form("change_password_form"):
        current_pwd = st.text_input("Current Password", type="password")
        new_pwd = st.text_input("New Password", type="password")
        confirm_pwd = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("🔄 Change Password"):
            if not current_pwd or not new_pwd:
                st.error("Please fill in all password fields")
            elif new_pwd != confirm_pwd:
                st.error("New passwords don't match")
            else:
                success, message = auth.change_password(org['id'], current_pwd, new_pwd)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # Logout button
    if st.button("🚪 Logout", type="secondary"):
        auth.logout()
        st.rerun()