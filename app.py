import streamlit as st
from modules import add_donor, dashboard, donor_info, record_donation, view_receipts, email_template
from modules.pdf_template import pdf_settings_page
from modules.data_export import export_data_page
from modules.settings import settings_page
from modules.airtable_utils import fetch_all_donations, fetch_donors

st.set_page_config(page_title="DearDonor - Nonprofit Management", layout="wide")

# Initialize session state for navigation
if 'navigation' not in st.session_state:
    st.session_state.navigation = "Home"

# Sidebar Navigation
st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", [
    "Home", 
    "Add Donor", 
    "Record Donation", 
    "Dashboard", 
    "Donor Info", 
    "View Receipts",
    "Email Settings",
    "PDF Settings",
    "Export Data",
    "Settings"
])

# Page Routing
if choice == "Home":
    st.title("🏠 Welcome to DearDonor")
    st.markdown("### Your Complete Nonprofit Management Solution")
    
    # Quick Stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Quick Statistics")
        donations = fetch_all_donations()
        donors = fetch_donors()
        
        total_donations = len(donations)
        total_donors = len(donors)
        total_amount = sum(d['amount'] for d in donations)
        
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            st.metric("Total Donors", f"{total_donors:,}")
            st.metric("Total Donations", f"{total_donations:,}")
        with stats_col2:
            st.metric("Total Amount", f"₹{total_amount:,.2f}")
    
    with col2:
        st.markdown("### 🎯 Key Features")
        st.markdown("""
        - **Donor Management**: Easily add and manage donor profiles
        - **Donation Tracking**: Record and monitor all donations
        - **Receipt Generation**: Automatic PDF receipt generation
        - **Email Integration**: Automated thank you emails
        - **Analytics**: Comprehensive donation analytics
        - **Data Export**: Export data in various formats
        """)
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    quick_action_cols = st.columns(3)
    
    with quick_action_cols[0]:
        st.markdown("""
        #### 👤 Donor Management
        - [Add New Donor](#add-donor)
        - [View Donor Profiles](#donor-info)
        - [Update Donor Information](#donor-info)
        """)
    
    with quick_action_cols[1]:
        st.markdown("""
        #### 💰 Donations
        - [Record New Donation](#record-donation)
        - [View All Donations](#view-receipts)
        - [Download Receipts](#view-receipts)
        """)
    
    with quick_action_cols[2]:
        st.markdown("""
        #### ⚙️ Settings & Reports
        - [Email Templates](#email-settings)
        - [PDF Settings](#pdf-settings)
        - [Export Data](#export-data)
        """)
    
    # Help Section
    st.markdown("### ❓ Need Help?")
    st.info("""
    **Getting Started:**
    1. First, add your donors using the 'Add Donor' page
    2. Record donations through the 'Record Donation' page
    3. View and analyze data in the 'Dashboard'
    4. Download receipts and manage emails as needed
    
    Use the navigation menu on the left to access all features.
    """)

elif choice == "Add Donor":
    add_donor.new_donor_view()

elif choice == "Record Donation":
    record_donation.record_donation_view()

elif choice == "Dashboard":
    dashboard.show_dashboard()

elif choice == "Donor Info":
    donor_info.view_donor_profile()

elif choice == "View Receipts":
    view_receipts.st_main()

elif choice == "Email Settings":
    email_template.email_settings_page()

elif choice == "PDF Settings":
    pdf_settings_page()

elif choice == "Export Data":
    export_data_page()

elif choice == "Settings":
    settings_page()