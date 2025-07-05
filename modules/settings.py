import streamlit as st
import json
import os
from datetime import datetime
from modules.supabase_utils import get_organization_settings, save_organization_settings, get_organization_asset_path
from modules.pdf_template import pdf_settings_page
from modules.email_template import email_settings_page
from modules.auth import OrganizationAuth

SETTINGS_FILE = "config/settings.json"

DEFAULT_SETTINGS = {
    "organization": {
        "name": "",
        "office_address": "",
        "phone": "",
        "email": "",
        "website": "",
        "registration_number": "",
        "pan_number": "",
        "csr_number": "",
        "tax_exemption_number": "",
        "social_media": {
            "facebook": "",
            "instagram": "",
            "youtube": ""
        },
        "signature_holder": {
            "name": "",
            "designation": ""
        }
    },
    "receipt_format": {
        "prefix": "DR",
        "format": "{prefix}/{YY}/{MM}/{XXX}",
        "next_sequence": 1
    },
    "donation_purposes": [
        "Corpus Fund",
        "General Operational Fund",
        "Construction Fund",
        "Education Fund",
        "Healthcare Fund"
    ]
}

def ensure_settings_file():
    """Ensure settings file exists with default values"""
    os.makedirs("config", exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
    return load_settings()

def load_settings():
    """Load settings from file and ensure all required structures exist - DEPRECATED: Use load_org_settings instead"""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            
            # Ensure organization structure exists
            if 'organization' not in settings:
                settings['organization'] = DEFAULT_SETTINGS['organization']
            
            # Ensure social_media structure exists
            if 'social_media' not in settings['organization']:
                settings['organization']['social_media'] = DEFAULT_SETTINGS['organization']['social_media']
            
            # Ensure receipt_format structure exists
            if 'receipt_format' not in settings:
                settings['receipt_format'] = DEFAULT_SETTINGS['receipt_format']
            
            # Ensure donation_purposes exists
            if 'donation_purposes' not in settings:
                settings['donation_purposes'] = DEFAULT_SETTINGS['donation_purposes']
            
            save_settings(settings)
            return settings
    except FileNotFoundError:
        return ensure_settings_file()

def save_settings(settings):
    """Save settings to file - DEPRECATED: Use save_org_settings instead"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_org_settings(organization_id: str = None):
    """Load organization-specific settings from database"""
    if not organization_id:
        # Try to get from session state
        if 'organization' in st.session_state:
            organization_id = st.session_state.organization['id']
        else:
            return DEFAULT_SETTINGS
    
    return get_organization_settings(organization_id)

def save_org_settings(settings: dict, organization_id: str = None):
    """Save organization-specific settings to database"""
    if not organization_id:
        # Try to get from session state
        if 'organization' in st.session_state:
            organization_id = st.session_state.organization['id']
        else:
            return False
    
    return save_organization_settings(organization_id, settings)

def settings_view():
    st.title("⚙️ Settings")
    
    # Get organization_id from session state
    if 'organization' not in st.session_state:
        st.error("❌ Organization not found. Please login again.")
        return
    
    organization_id = st.session_state.organization['id']
    
    # Load current settings from database
    settings = load_org_settings(organization_id)
    
    # Create tabs for different settings
    general_tab, receipt_tab, signature_tab, purposes_tab, pdf_tab, email_tab = st.tabs([
        "📝 General Information", 
        "🧾 Receipt Format",
        "✍️ Signature Settings",
        "🎯 Donation Purposes",
        "📄 PDF Template",
        "✉️ Email Settings"
    ])
    
    with general_tab:
        st.header("Organization Information")
        
        # Organization details form
        org_name = st.text_input(
            "Organization Name *",
            value=settings.get('organization', {}).get('name', ''),
            help="Your organization's registered name"
        )
        
        office_address = st.text_area(
            "Office Address *",
            value=settings.get('organization', {}).get('office_address', ''),
            help="Complete office address"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input(
                "Phone Number *",
                value=settings.get('organization', {}).get('phone', ''),
                help="Primary contact number"
            )
        with col2:
            email = st.text_input(
                "Email Address *",
                value=settings.get('organization', {}).get('email', ''),
                help="Primary contact email"
            )
            
            website = st.text_input(
                "Website",
            value=settings.get('organization', {}).get('website', ''),
            help="Organization website URL"
            )
        
        # Registration details
        st.subheader("Registration Details")
        
        col1, col2 = st.columns(2)
        with col1:
            reg_no = st.text_input(
                "Registration Number *",
                value=settings.get('organization', {}).get('registration_number', ''),
                help="Trust registration number"
            )
            
            pan_no = st.text_input(
                "PAN Number *",
                value=settings.get('organization', {}).get('pan_number', ''),
                help="Organization PAN number"
            )
        
        with col2:
            csr_no = st.text_input(
                "CSR Number",
                value=settings.get('organization', {}).get('csr_number', ''),
                help="CSR registration number"
            )
            
            tax_exempt_no = st.text_input(
                "Tax Exemption Number",
                value=settings.get('organization', {}).get('tax_exemption_number', ''),
                help="80G registration number"
            )
        
        # Social media links
        st.subheader("Social Media")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            facebook = st.text_input(
                "Facebook",
                value=settings.get('organization', {}).get('social_media', {}).get('facebook', ''),
                help="Facebook page URL"
            )
        with col2:
            instagram = st.text_input(
                "Instagram",
                value=settings.get('organization', {}).get('social_media', {}).get('instagram', ''),
                help="Instagram profile URL"
            )
        with col3:
            youtube = st.text_input(
                "YouTube",
                value=settings.get('organization', {}).get('social_media', {}).get('youtube', ''),
                help="YouTube channel URL"
            )
        
        if st.button("Save General Information"):
            settings['organization'] = {
                "name": org_name,
                "office_address": office_address,
                "phone": phone,
                "email": email,
                "website": website,
                "registration_number": reg_no,
                "pan_number": pan_no,
                "csr_number": csr_no,
                "tax_exemption_number": tax_exempt_no,
                "social_media": {
                    "facebook": facebook,
                    "instagram": instagram,
                    "youtube": youtube
                },
                "signature_holder": settings.get('organization', {}).get('signature_holder', DEFAULT_SETTINGS['organization']['signature_holder'])

            }
            if save_org_settings(settings, organization_id):
                st.success("✅ Organization information saved successfully!")
            else:
                st.error("❌ Failed to save organization information.")
        
        st.markdown("---")
        
        # Password change section
        st.subheader("🔐 Change Password")
        st.markdown("Update your organization account password")
        
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
                    auth = OrganizationAuth()
                    success, message = auth.change_password(organization_id, current_pwd, new_pwd)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
    
    with receipt_tab:
        st.header("Receipt Number Format")
        st.markdown("""
        Configure how your receipt numbers are generated. This format will be used for all donation receipts.
        
        Available placeholders:
        - `{prefix}` - Receipt prefix (e.g., DR, REC)
        - `{YY}` - Last two digits of the year
        - `{MM}` - Two-digit month
        - `{XXX}` - Sequential number (automatically incremented)
        """)
        
        receipt_col1, receipt_col2 = st.columns(2)
        with receipt_col1:
            receipt_prefix = st.text_input(
                "Receipt Number Prefix",
                value=settings.get('receipt_format', {}).get('prefix', DEFAULT_SETTINGS['receipt_format']['prefix']),
                help="Short prefix for receipt numbers (e.g., DR, REC, DON)"
            )
        with receipt_col2:
            receipt_format = st.text_input(
                "Receipt Number Format",
                value=settings.get('receipt_format', {}).get('format', DEFAULT_SETTINGS['receipt_format']['format']),
                help="Format string using {prefix}, {YY} (year), {MM} (month), {XXX} (sequence)"
            )
        
        # Example receipt number
        current_date = datetime.now()
        year_short = str(current_date.year)[-2:]
        month = str(current_date.month).zfill(2)
        example = receipt_format.format(
            prefix=receipt_prefix,
            YY=year_short,
            MM=month,
            XXX="001"
        )
        st.info(f"Example receipt number: {example}")
        
        if st.button("Save Receipt Format"):
            settings['receipt_format'] = {
                "prefix": receipt_prefix,
                "format": receipt_format,
                "next_sequence": settings.get('receipt_format', {}).get('next_sequence', 1)
            }
            if save_org_settings(settings, organization_id):
                st.success("✅ Receipt format saved successfully!")
            else:
                st.error("❌ Failed to save receipt format.")
            
    with signature_tab:
        st.header("Signature Settings")
        st.markdown("""
        Configure the signature holder details that will appear on all receipts and certificates.
        """)
        
        signature_col1, signature_col2 = st.columns(2)
        with signature_col1:
            signature_name = st.text_input(
                "Signature Holder Name *",
                value=settings.get('organization', {}).get('signature_holder', {}).get('name', ''),
                help="Name of the person signing the documents"
            )
        with signature_col2:
            signature_designation = st.text_input(
                "Designation *",
                value=settings.get('organization', {}).get('signature_holder', {}).get('designation', ''),
                help="Designation of the signature holder"
            )
            
        if st.button("Save Signature Settings"):
            if not settings.get('organization'):
                settings['organization'] = {}
            
            # Update signature holder info
            settings['organization']['signature_holder'] = {
                "name": signature_name,
                "designation": signature_designation
            }
            if save_org_settings(settings, organization_id):
                st.success("✅ Signature settings saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save signature settings.")
    
    with purposes_tab:
        st.header("Common Donation Purposes")
        st.markdown("""
        Define common donation purposes to avoid repeated typing in the donation form. 
        These will appear as quick selections when recording donations.
        """)
        
        # Custom CSS for delete buttons and layout
        st.markdown("""
            <style>
            [data-testid="stButton"] > button[kind="secondary"] {
                background-color: #dc3545 !important;
                border-color: #dc3545 !important;
                color: white !important;
            }
            [data-testid="stButton"] > button[kind="secondary"]:hover {
                background-color: #c82333 !important;
                border-color: #bd2130 !important;
                color: white !important;
            }
            /* Remove padding from columns */
            [data-testid="column"] {
                padding: 0 !important;
                margin: 0 !important;
            }
            /* Add spacing between purpose rows */
            [data-testid="stHorizontalBlock"] {
                margin-bottom: 0.5rem !important;
                gap: 0.5rem !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Display current purposes
        st.subheader("Current Purposes")
        purposes = settings.get("donation_purposes", [])
        
        # Initialize session state for purposes if not exists
        if 'purposes' not in st.session_state:
            st.session_state.purposes = purposes.copy()
        
        # Edit existing purposes
        updated_purposes = []
        for i, purpose in enumerate(st.session_state.purposes):
            cols = st.columns([0.85, 0.15])  # Adjust ratio for better alignment
            with cols[0]:
                updated_purpose = st.text_input(f"Purpose {i+1}", value=purpose, key=f"purpose_{i}", label_visibility="collapsed")
                if updated_purpose.strip():  # Only add non-empty purposes
                    updated_purposes.append(updated_purpose)
            with cols[1]:
                if st.button("🗑️ Delete", key=f"delete_{i}", type="secondary", use_container_width=True):
                    # Remove the purpose from session state
                    st.session_state.purposes.pop(i)
                    # Update settings
                    settings["donation_purposes"] = st.session_state.purposes
                    save_org_settings(settings, organization_id)
                    st.rerun()
        
        # Add new purpose
        st.subheader("Add New Purpose")
        new_purpose = st.text_input("New Purpose", key="new_purpose_input", label_visibility="collapsed")
        
        # Add Purpose button
        if st.button("Add Purpose", type="primary", use_container_width=True, key="add_purpose_btn"):
            if new_purpose.strip():
                st.session_state.purposes.append(new_purpose.strip())
                # Update settings immediately
                settings["donation_purposes"] = st.session_state.purposes
                save_org_settings(settings, organization_id)
                st.success("✅ New purpose added successfully!")
                st.rerun()
        
        # Save all changes
        if st.button("Save Donation Purposes", type="primary", use_container_width=True, key="save_purposes_btn"):
            # Filter out empty purposes
            updated_purposes = [p for p in updated_purposes if p.strip()]
            st.session_state.purposes = updated_purposes
            settings["donation_purposes"] = updated_purposes
            if save_org_settings(settings, organization_id):
                st.success("✅ Donation purposes saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save donation purposes.")
    
    with pdf_tab:
        # Call the PDF settings page function from pdf_template module
        pdf_settings_page()
    
    with email_tab:
        # Call the email settings page function from email_template module
        email_settings_page() 