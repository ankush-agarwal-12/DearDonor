import streamlit as st
import os

def read_markdown_file(file_path):
    """Read and return the content of a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Replace ::: syntax with div tags
            content = content.replace(':::feature-card', '<div class="feature-card">')
            content = content.replace(':::tip-card', '<div class="tip-card">')
            content = content.replace(':::warning-card', '<div class="warning-card">')
            content = content.replace(':::', '</div>')
            return content
    except FileNotFoundError:
        return "Documentation file not found."

def user_guide_view():
    user_guide_content = read_markdown_file("docs/user_guide.md")
    st.markdown(user_guide_content, unsafe_allow_html=True)

def faqs_view():
    faq_content = read_markdown_file("docs/faq.md")
    st.markdown(faq_content, unsafe_allow_html=True)

def support_view():
    support_content = read_markdown_file("docs/support.md")
    st.markdown(support_content, unsafe_allow_html=True)

def documentation_view():
    # Add custom CSS for documentation styling
    st.markdown("""
        <style>
        /* Main Documentation Styles */
        .main-header {
            font-size: 2.8rem;
            font-weight: 700;
            color: #1E88E5;
            margin-bottom: 1rem;
            text-align: center;
            padding: 2rem 0;
        }
        
        .sub-header {
            font-size: 1.2rem;
            color: #424242;
            text-align: center;
            margin-bottom: 3rem;
        }
        
        /* Section Styles */
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E88E5;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e0e0e0;
        }
        
        h2 {
            font-size: 1.8rem;
            font-weight: 600;
            color: #2196F3;
            margin: 1.5rem 0 1rem 0;
        }
        
        h3 {
            font-size: 1.4rem;
            font-weight: 600;
            color: #1976D2;
            margin: 1.2rem 0 0.8rem 0;
        }
        
        /* Content Styles */
        p {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #424242;
            margin: 1rem 0;
        }
        
        ul, ol {
            margin: 1rem 0;
            padding-left: 2rem;
        }
        
        li {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #424242;
            margin: 0.5rem 0;
        }
        
        /* Card Styles */
        .feature-card {
            background-color: #ffffff;
            border-radius: 0.8rem;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .tip-card {
            background-color: #E3F2FD;
            border-radius: 0.8rem;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #BBDEFB;
        }
        
        .warning-card {
            background-color: #FFF3E0;
            border-radius: 0.8rem;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #FFE0B2;
        }
        
        /* Code Block Styles */
        code {
            font-family: 'Roboto Mono', monospace;
            background-color: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 0.3rem;
            font-size: 0.9rem;
            color: #1565C0;
        }
        
        pre {
            background-color: #f5f5f5;
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            margin: 1rem 0;
        }
        
        /* Link Styles */
        a {
            color: #1E88E5;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-bottom-color 0.2s;
        }
        
        a:hover {
            border-bottom-color: #1E88E5;
        }
        
        /* Table Styles */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background-color: #ffffff;
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        th {
            background-color: #f5f5f5;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #1E88E5;
            border-bottom: 2px solid #e0e0e0;
        }
        
        td {
            padding: 1rem;
            border-bottom: 1px solid #e0e0e0;
            color: #424242;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 1.5rem;
            color: #424242;
            border-radius: 0.5rem;
            background-color: transparent;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #E3F2FD !important;
            color: #1E88E5 !important;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2.2rem;
                padding: 1.5rem 0;
            }
            
            .sub-header {
                font-size: 1rem;
                margin-bottom: 2rem;
            }
            
            h1 { font-size: 2rem; }
            h2 { font-size: 1.6rem; }
            h3 { font-size: 1.3rem; }
            p, li { font-size: 1rem; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Documentation Header
    st.markdown('<h1 class="main-header">📚 DearDonor Documentation</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your comprehensive guide to managing nonprofit donations effectively</p>', unsafe_allow_html=True)
    
    # Create tabs for different documentation sections
    tab_names = ["User Guide", "FAQs", "Support"]
    tabs = st.tabs(tab_names)
    
    # Show the appropriate content based on the selected tab
    with tabs[0]:  # User Guide
        user_guide_view()
    
    with tabs[1]:  # FAQs
        faqs_view()
    
    with tabs[2]:  # Support
        support_view()

    # Tips and Best Practices
    st.markdown("### 💡 Tips and Best Practices")
    st.markdown("""
    <div class="tip-card">
    
    **For Optimal Use:**
    - Regularly backup your data using the export feature
    - Keep donor information updated
    - Use meaningful descriptions for donations
    - Regularly check recurring donation schedules
    - Test email templates before sending
    </div>
    """, unsafe_allow_html=True)

    # Important Notes
    st.markdown("### ⚠️ Important Notes")
    st.markdown("""
    <div class="warning-card">
    
    **Please Note:**
    - All donation amounts are in INR (₹)
    - Recurring donations can be modified until the next due date
    - Cancelled recurring donations cannot be reactivated
    - Keep your email template variables updated
    - Regular data backups are recommended
    </div>
    """, unsafe_allow_html=True)

    # Support Information
    st.markdown("### 🆘 Need Help?")
    st.markdown("""
    For additional support:
    - Email: support@deardonor.com
    - Visit our Help Center: [help.deardonor.com](https://help.deardonor.com)
    - Documentation Updates: Check regularly for feature updates
    """) 