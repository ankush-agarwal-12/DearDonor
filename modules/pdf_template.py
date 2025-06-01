import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os
from dotenv import load_dotenv
import json
from PIL import Image
import io

load_dotenv()

# Default receipt template settings
DEFAULT_RECEIPT_SETTINGS = {
    "header_color": "#000000",
    "accent_color": "#4A90E2",
    "font_family": "Helvetica",
    "logo_position": "left",
    "show_border": True,
    "border_color": "#000000",
    "include_signature": True,
    "signature_position": "bottom-right",
    "footer_text": "*Subject to encashment of cheque",
    "layout": "classic",  # classic, modern, minimal
    "org_name": "THE STRAY ARMY CHARITABLE TRUST",
    "reg_no": "2022/SR/1732/BK4/109, SEA2335753221801",
    "office_address": "Flat No. 218, 2nd Floor, Block-A, Triveni Bhaskar City, Pardih Main Road, Mango, Jamshedpur, Jharkhand - 831012",
    "pan_no": "AAETT3091Q",
    "csr_no": "CSR00072375",
    "phone": "7609874246",
    "email": "thestrayarmy@gmail.com",
    "website": "www.thestrayarmy.com"
}

# Default thank you note settings
DEFAULT_THANKYOU_SETTINGS = {
    "theme": "butterflies",  # butterflies, minimal, professional
    "color_scheme": "warm",  # warm, cool, monochrome
    "include_image": True,
    "image_style": "illustration",  # illustration, photo, none
    "font_style": "cursive",  # cursive, modern, classic
    "border_style": "elegant",  # elegant, simple, none
    "show_logo": True,
    "include_signature": True
}

def save_pdf_settings(receipt_settings=None, thankyou_settings=None, enable_thankyou=True):
    """Save PDF template settings to .env file"""
    settings = {}
    if receipt_settings:
        settings['PDF_RECEIPT_SETTINGS'] = json.dumps(receipt_settings)
    if thankyou_settings is not None:  # Could be False
        settings['PDF_THANKYOU_SETTINGS'] = json.dumps(thankyou_settings)
    settings['ENABLE_THANKYOU_NOTES'] = str(enable_thankyou)
    
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or add settings
    for key, value in settings.items():
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}="{value}"\n'
                key_found = True
                break
        if not key_found:
            lines.append(f'{key}="{value}"\n')

    with open(env_path, 'w') as f:
        f.writelines(lines)

def get_pdf_settings():
    """Get current PDF template settings"""
    receipt_settings = os.getenv('PDF_RECEIPT_SETTINGS')
    thankyou_settings = os.getenv('PDF_THANKYOU_SETTINGS')
    enable_thankyou = os.getenv('ENABLE_THANKYOU_NOTES', 'True').lower() == 'true'
    
    return {
        'receipt': json.loads(receipt_settings) if receipt_settings else DEFAULT_RECEIPT_SETTINGS,
        'thankyou': json.loads(thankyou_settings) if thankyou_settings else DEFAULT_THANKYOU_SETTINGS,
        'enable_thankyou': enable_thankyou
    }

def pdf_settings_page():
    st.title("📄 PDF Template Settings")
    
    # Get current settings
    current_settings = get_pdf_settings()
    
    # Create tabs for Organization Info, Receipt Template, and Thank You Note
    org_tab, receipt_tab, thankyou_tab = st.tabs(["Organization Info", "Receipt Template", "Thank You Note"])
    
    with org_tab:
        st.subheader("Organization Information")
        
        # Logo upload
        st.markdown("### Organization Logo")
        logo_col1, logo_col2 = st.columns([2, 1])
        with logo_col1:
            uploaded_logo = st.file_uploader("Upload your organization logo (PNG or JPG)", type=['png', 'jpg', 'jpeg'])
            if uploaded_logo:
                # Save the uploaded logo
                logo_image = Image.open(uploaded_logo)
                logo_image.save("assets/logo.png")
                st.success("✅ Logo uploaded successfully!")
        with logo_col2:
            if os.path.exists("assets/logo.png"):
                st.image("assets/logo.png", caption="Current Logo", width=150)
        
        # Signature upload
        st.markdown("### Digital Signature")
        sig_col1, sig_col2 = st.columns([2, 1])
        with sig_col1:
            uploaded_signature = st.file_uploader("Upload your digital signature (PNG with transparent background)", type=['png'])
            if uploaded_signature:
                # Save the uploaded signature
                sig_image = Image.open(uploaded_signature)
                sig_image.save("assets/signature.png")
                st.success("✅ Signature uploaded successfully!")
        with sig_col2:
            if os.path.exists("assets/signature.png"):
                st.image("assets/signature.png", caption="Current Signature", width=150)
        
        # Organization Details
        st.markdown("### Organization Details")
        org_col1, org_col2 = st.columns(2)
        
        with org_col1:
            org_name = st.text_input("Organization Name", current_settings['receipt'].get('org_name', DEFAULT_RECEIPT_SETTINGS['org_name']))
            reg_no = st.text_input("Registration Number", current_settings['receipt'].get('reg_no', DEFAULT_RECEIPT_SETTINGS['reg_no']))
            office_address = st.text_area("Office Address", current_settings['receipt'].get('office_address', DEFAULT_RECEIPT_SETTINGS['office_address']))
            pan_no = st.text_input("PAN Number", current_settings['receipt'].get('pan_no', DEFAULT_RECEIPT_SETTINGS['pan_no']))
        
        with org_col2:
            csr_no = st.text_input("CSR Number", current_settings['receipt'].get('csr_no', DEFAULT_RECEIPT_SETTINGS['csr_no']))
            phone = st.text_input("Phone Number", current_settings['receipt'].get('phone', DEFAULT_RECEIPT_SETTINGS['phone']))
            email = st.text_input("Email", current_settings['receipt'].get('email', DEFAULT_RECEIPT_SETTINGS['email']))
            website = st.text_input("Website", current_settings['receipt'].get('website', DEFAULT_RECEIPT_SETTINGS['website']))
    
    with receipt_tab:
        st.subheader("Donation Receipt Template")
        
        # Template Style Selection
        st.markdown("### Choose Template Style")
        receipt_style = st.radio(
            "Select a template style:",
            options=["Classic", "Modern", "Minimal"],
            index=["classic", "modern", "minimal"].index(current_settings['receipt']['layout'])
        )
        
        # Preview current template
        st.markdown("### Receipt Preview")
        if st.checkbox("Show Preview", value=True):
            preview_col1, preview_col2 = st.columns([2, 1])
            with preview_col1:
                st.image("assets/receipt_preview.png", caption=f"{receipt_style} Style Preview")
            with preview_col2:
                st.markdown("#### Key Features:")
                st.markdown("""
                - Professional layout
                - Complete organization details
                - Clear information hierarchy
                - Secure design elements
                """)
        
        # Customization Options
        st.markdown("### Customize Template")
        custom_col1, custom_col2 = st.columns(2)
        
        with custom_col1:
            header_color = st.color_picker(
                "Header Color",
                current_settings['receipt']['header_color']
            )
            accent_color = st.color_picker(
                "Accent Color",
                current_settings['receipt']['accent_color']
            )
            font_family = st.selectbox(
                "Font Family",
                ["Helvetica", "Times New Roman", "Arial"],
                index=["Helvetica", "Times New Roman", "Arial"].index(
                    current_settings['receipt']['font_family']
                )
            )
        
        with custom_col2:
            logo_position = st.selectbox(
                "Logo Position",
                ["Left", "Right", "Center"],
                index=["left", "right", "center"].index(
                    current_settings['receipt']['logo_position']
                )
            )
            show_border = st.checkbox(
                "Show Border",
                value=current_settings['receipt']['show_border']
            )
            include_signature = st.checkbox(
                "Include Digital Signature",
                value=current_settings['receipt']['include_signature']
            )
    
    with thankyou_tab:
        st.subheader("Thank You Note Template")
        
        # Enable/Disable Thank You Notes
        enable_thankyou = st.checkbox(
            "Enable Thank You Notes with Receipts",
            value=current_settings['enable_thankyou'],
            help="When enabled, a thank you note will be included with the donation receipt"
        )
        
        if enable_thankyou:
            # Theme Selection
            st.markdown("### Choose Theme")
            thankyou_theme = st.radio(
                "Select a theme:",
                options=["Butterflies", "Minimal", "Professional"],
                index=["butterflies", "minimal", "professional"].index(
                    current_settings['thankyou']['theme']
                )
            )
            
            # Preview current theme
            st.markdown("### Thank You Note Preview")
            if st.checkbox("Show Thank You Preview", value=True):
                preview_col1, preview_col2 = st.columns([2, 1])
                with preview_col1:
                    st.image("assets/thankyou_preview.png", caption=f"{thankyou_theme} Theme Preview")
                with preview_col2:
                    st.markdown("#### Theme Features:")
                    st.markdown("""
                    - Elegant design
                    - Personalized message
                    - Professional layout
                    - High-quality graphics
                    """)
            
            # Customization Options
            st.markdown("### Customize Theme")
            custom_col1, custom_col2 = st.columns(2)
            
            with custom_col1:
                color_scheme = st.selectbox(
                    "Color Scheme",
                    ["Warm", "Cool", "Monochrome"],
                    index=["warm", "cool", "monochrome"].index(
                        current_settings['thankyou']['color_scheme']
                    )
                )
                font_style = st.selectbox(
                    "Font Style",
                    ["Cursive", "Modern", "Classic"],
                    index=["cursive", "modern", "classic"].index(
                        current_settings['thankyou']['font_style']
                    )
                )
            
            with custom_col2:
                border_style = st.selectbox(
                    "Border Style",
                    ["Elegant", "Simple", "None"],
                    index=["elegant", "simple", "none"].index(
                        current_settings['thankyou']['border_style']
                    )
                )
                show_logo = st.checkbox(
                    "Show Organization Logo",
                    value=current_settings['thankyou']['show_logo']
                )
    
    # Save Settings
    if st.button("💾 Save Template Settings"):
        # Update settings
        receipt_settings = {
            "header_color": header_color,
            "accent_color": accent_color,
            "font_family": font_family,
            "logo_position": logo_position.lower(),
            "show_border": show_border,
            "border_color": current_settings['receipt']['border_color'],
            "include_signature": include_signature,
            "signature_position": current_settings['receipt']['signature_position'],
            "footer_text": current_settings['receipt']['footer_text'],
            "layout": receipt_style.lower(),
            "org_name": org_name,
            "reg_no": reg_no,
            "office_address": office_address,
            "pan_no": pan_no,
            "csr_no": csr_no,
            "phone": phone,
            "email": email,
            "website": website
        }
        
        thankyou_settings = {
            "theme": thankyou_theme.lower(),
            "color_scheme": color_scheme.lower(),
            "include_image": current_settings['thankyou']['include_image'],
            "image_style": current_settings['thankyou']['image_style'],
            "font_style": font_style.lower(),
            "border_style": border_style.lower(),
            "show_logo": show_logo,
            "include_signature": current_settings['thankyou']['include_signature']
        } if enable_thankyou else None
        
        save_pdf_settings(receipt_settings, thankyou_settings, enable_thankyou)
        st.success("✅ Template settings saved successfully!")
        
    # Reset to Default
    if st.button("🔄 Reset to Default"):
        save_pdf_settings(DEFAULT_RECEIPT_SETTINGS, DEFAULT_THANKYOU_SETTINGS, True)
        st.rerun() 