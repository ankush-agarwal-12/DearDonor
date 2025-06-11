import streamlit as st
from modules.add_donor import add_donor_view
from modules.record_donation import record_donation_view
from modules.donor_info import donor_info_view
from modules.dashboard import dashboard_view
from modules.view_receipts import view_receipts_view
from modules.data_export import data_export_view
from modules.settings import settings_view
from modules.supabase_utils import fetch_all_donations, fetch_donors
from modules import add_donor, dashboard, donor_info, record_donation, email_template
from modules.pdf_template import pdf_settings_page
from modules.documentation import documentation_view
from modules.recurring_donations import recurring_donations_view

# Page configuration
st.set_page_config(
    page_title="DearDonor - Nonprofit Management",
    page_icon="🎗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    /* Main app styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1E88E5;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    section[data-testid="stSidebar"] > div {
        padding: 2rem 1rem;
    }
    
    /* App title styling */
    .app-title {
        text-align: center;
        padding: 0.75rem 0 1.5rem 0;
        border-bottom: 1px solid #e9ecef;
        margin-bottom: 1.5rem;
    }
    .app-title h1 {
        color: #1E88E5;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .app-title p {
        color: #666;
        font-size: 0.9rem;
        margin: 0;
    }
    
    /* Remove default button styling */
    .stButton {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0.25rem 0 !important;
    }

    /* Custom button styling */
    .stButton > button {
        width: 100% !important;
        background: transparent !important;
        border: 1px solid #1E88E5 !important;
        color: #1E88E5 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.95rem !important;
        border-radius: 0.5rem !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 0.5rem !important;
        text-align: left !important;
        line-height: 1.5 !important;
        margin: 0.25rem 0 !important;
    }

    /* Button hover state */
    .stButton > button:hover {
        background-color: rgba(30, 136, 229, 0.1) !important;
        transform: translateX(4px);
    }

    /* Button active state */
    .stButton > button:active {
        transform: translateX(4px) scale(0.98);
    }

    /* Selected button state */
    .stButton > button[data-testid="baseButton-secondary"] {
        background-color: #1E88E5 !important;
        color: white !important;
        border-color: #1E88E5 !important;
    }
    
    /* Navigation sections */
    .nav-section {
        margin-bottom: 1.5rem;
        padding: 0 0.5rem;
    }
    .nav-header {
        color: #6c757d;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
        padding-left: 0.5rem;
    }
    .nav-divider {
        height: 1px;
        background-color: #e9ecef;
        margin: 1.5rem 0;
    }
    
    /* App version footer */
    .app-version {
        position: relative;
        padding: 1.5rem;
        margin-top: 2rem;
        font-size: 0.8rem;
        color: #6c757d;
        text-align: center;
        border-top: 1px solid #e9ecef;
    }
    .app-version a {
        color: #1E88E5;
        text-decoration: none;
    }
    .app-version a:hover {
        text-decoration: underline;
    }
    
    /* Icon styling */
    .nav-icon {
        margin-right: 0.75rem;
        font-size: 1.1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Button icon spacing */
    .stButton > button {
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }
    .stButton > button > div {
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }
    
    /* Add extra margin to last nav section */
    .nav-section:last-child {
        margin-bottom: 8rem;
    }
    
    /* Additional overrides for Streamlit buttons */
    .stButton > button:hover {
        border-color: #1E88E5 !important;
        background-color: rgba(30, 136, 229, 0.1) !important;
        color: #1E88E5 !important;
    }
    
    /* Force transparent background */
    .stButton > button, 
    .stButton > button:focus,
    .stButton > button:active {
        background-color: transparent !important;
        background-image: none !important;
    }
    
    /* Override Streamlit's default styles */
    .stButton > button[kind="primary"],
    .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        background-image: none !important;
    }
    
    /* Remove any default backgrounds */
    .element-container,
    .stButton,
    .stMarkdown {
        background: transparent !important;
    }

    /* Override Streamlit's default button styles */
    div[data-testid="stHorizontalBlock"] button[kind="primary"],
    div[data-testid="stVerticalBlock"] button[kind="primary"],
    .stButton button[kind="primary"],
    .element-container .stButton button {
        background-color: #ffffff !important;
        border: 1px solid #1E88E5 !important;
        color: #1E88E5 !important;
    }

    div[data-testid="stHorizontalBlock"] button[kind="secondary"],
    div[data-testid="stVerticalBlock"] button[kind="secondary"],
    .stButton button[kind="secondary"],
    .element-container .stButton button[data-testid="baseButton-secondary"] {
        background-color: #1E88E5 !important;
        color: #ffffff !important;
        border: 1px solid #1E88E5 !important;
    }

    /* Remove any background images that might be interfering */
    .stButton button {
        background-image: none !important;
    }

    /* Force white background on all buttons */
    button[class*="st"] {
        background-color: #ffffff !important;
    }

    /* Additional override for any Streamlit-specific button classes */
    .st-emotion-cache-1r6slb0 button,
    .st-emotion-cache-1r6slb0 .stButton button {
        background-color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for navigation
if 'navigation' not in st.session_state:
    st.session_state['navigation'] = "Dashboard"

# Define navigation options
core_options = {
    "Dashboard": {"icon": "🏠", "tooltip": "Overview of donations and key metrics"},
    "Add Donor": {"icon": "➕", "tooltip": "Register new donors in the system"},
    "Record Donation": {"icon": "💰", "tooltip": "Record new donations from donors"},
    "Recurring Donations": {"icon": "🔄", "tooltip": "Manage recurring donation schedules"},
    "Donor Info": {"icon": "👥", "tooltip": "View and manage donor information"},
    "View Receipts": {"icon": "📄", "tooltip": "Access and manage donation receipts"},
    "Data Export": {"icon": "📤", "tooltip": "Export donation and donor data"}
}

settings_options = {
    "General Settings": {"icon": "⚙️", "tooltip": "Configure organization and general settings"},
    "Email Settings": {"icon": "📧", "tooltip": "Configure email templates and settings"},
    "PDF Settings": {"icon": "📑", "tooltip": "Customize receipt templates"},
    "Documentation": {"icon": "📚", "tooltip": "Access help and documentation"}
}

# Sidebar Navigation
with st.sidebar:
    # App Logo/Title
    st.markdown(
        '<div class="app-title">'
        '<h1>🎗️ DearDonor</h1>'
        '<p>Nonprofit Management System</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # Core Features Section
    for option, details in core_options.items():
        button_type = "secondary" if st.session_state['navigation'] == option else "primary"
        button_label = f"{details['icon']} {option}"
        if st.button(
            button_label,
            key=f"nav_{option}",
            use_container_width=True,
            type=button_type,
            help=details['tooltip']
        ):
            st.session_state['navigation'] = option
            st.rerun()

    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

    # Settings Section
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown('<div class="nav-header">Settings & Help</div>', unsafe_allow_html=True)
    
    for option, details in settings_options.items():
        button_type = "secondary" if st.session_state['navigation'] == option else "primary"
        button_label = f"{details['icon']} {option}"
        if st.button(
            button_label,
            key=f"nav_{option}",
            use_container_width=True,
            type=button_type,
            help=details['tooltip']
        ):
            st.session_state['navigation'] = option
            st.rerun()

    # Version info and credits at the bottom
    st.markdown(
        '<div class="app-version">'
        '<p>DearDonor v1.0.0</p>'
        '<p>Made with ❤️ by <a href="https://kapsco.in">Kaps Co.</a></p>'
        '<p>© 2025 Kaps Co.</p>'
        '</div>',
        unsafe_allow_html=True
    )

# Main content area
selected = st.session_state['navigation']

if selected == "Dashboard":
    dashboard_view()
elif selected == "Add Donor":
    add_donor_view()
elif selected == "Record Donation":
    record_donation_view()
elif selected == "Recurring Donations":
    recurring_donations_view()
elif selected == "Donor Info":
    donor_info_view()
elif selected == "View Receipts":
    view_receipts_view()
elif selected == "Data Export":
    data_export_view()
elif selected == "General Settings":
    settings_view()
elif selected == "Email Settings":
    email_template.email_settings_page()
elif selected == "PDF Settings":
    pdf_settings_page()
elif selected == "Documentation":
    documentation_view()

# Hide Streamlit footer
st.markdown(
    """
    <style>
    footer {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True
)