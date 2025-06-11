import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle, Image, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os
from dotenv import load_dotenv
import json
from PIL import Image
import io
from num2words import num2words
from datetime import datetime
from reportlab.lib.units import inch

load_dotenv()

# Use built-in fonts
FONT_NORMAL = 'Times-Roman'
FONT_BOLD = 'Times-Bold'
FONT_HEADING = 'Helvetica-Bold'

# Default receipt template settings
DEFAULT_RECEIPT_SETTINGS = {
    "margin": 40,
    "signature_holder": {
        "name": "Piyush Agarwal",
        "designation": "Founder"
    }
}

class DonationReceipt:
    def __init__(self, donor_data, org_settings):
        self.donor_data = donor_data
        self.org_settings = org_settings
        self.width, self.height = A4
        self.margin = DEFAULT_RECEIPT_SETTINGS['margin']
        
    def format_amount(self, amount):
        """Format amount with Rs. prefix and commas"""
        try:
            amount_float = float(amount)
            return f"Rs. {amount_float:,.2f}"
        except:
            return f"Rs. {amount}"
            
    def amount_to_words(self, amount):
        """Convert amount to words in Indian style"""
        try:
            amount_float = float(amount)
            words = num2words(amount_float, lang='en_IN').title()
            return f"Rupees {words} Only"
        except:
            return str(amount)
        
    def generate(self, output_path):
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # Set up coordinates
        left_margin = self.margin
        right_margin = self.width - self.margin
        top_margin = self.height - self.margin
        current_y = top_margin
        
        # Add logo
        try:
            logo_path = "assets/logo.png"
            if os.path.exists(logo_path):
                logo_width = 1.2 * inch
                logo_height = 1.2 * inch
                c.drawImage(logo_path, left_margin, current_y - logo_height + 0.2*inch, 
                          width=logo_width, height=logo_height, preserveAspectRatio=True)
                logo_space = 1.5 * inch
            else:
                logo_space = 0
        except:
            logo_space = 0
        
        # Calculate center position
        center_x = self.width / 2
        
        # Organization Name (centered, larger font)
        c.setFont(FONT_HEADING, 14)
        org_name = self.org_settings['name'].upper()
        org_name_width = c.stringWidth(org_name, FONT_HEADING, 14)
        c.drawString(center_x - (org_name_width/2), current_y, org_name)
        
        # Registration details (centered, normal font)
        current_y -= 20  # Increased spacing
        c.setFont(FONT_NORMAL, 10)
        reg_text = f"Registered Under Indian Trusts Act, 1882. (Reg No. - {self.org_settings['registration_number']})"
        reg_width = c.stringWidth(reg_text, FONT_NORMAL, 10)
        c.drawString(center_x - (reg_width/2), current_y, reg_text)
        
        # Office Address
        current_y -= 20  # Consistent spacing
        office_text = f"Office - {self.org_settings['office_address']}"
        office_width = c.stringWidth(office_text, FONT_NORMAL, 10)
        c.drawString(center_x - (office_width/2), current_y, office_text)
        
        # PAN and CSR (centered)
        current_y -= 20
        pan_csr_text = f"PAN - {self.org_settings['pan_number']} | CSR No. - {self.org_settings['csr_number']}"
        pan_csr_width = c.stringWidth(pan_csr_text, FONT_NORMAL, 10)
        c.drawString(center_x - (pan_csr_width/2), current_y, pan_csr_text)
        
        # Contact info (centered)
        current_y -= 20  # Consistent spacing
        contact_text = f"Phone: {self.org_settings['phone']} | Email: {self.org_settings['email']} | {self.org_settings['website']}"
        contact_width = c.stringWidth(contact_text, FONT_NORMAL, 10)
        c.drawString(center_x - (contact_width/2), current_y, contact_text)
        
        # Add extra spacing before the divider
        current_y -= 25
        
        # Horizontal line divider (thin gray)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)  # Light gray color
        c.setLineWidth(0.5)  # Thin line
        c.line(left_margin, current_y, right_margin, current_y)
        
        # Add spacing after the divider
        current_y -= 30
        
        # Receipt number and date
        c.setFont(FONT_NORMAL, 11)
        c.setFillColor(colors.black)  # Reset to black color for text
        receipt_no = self.donor_data.get('receipt_number', '')
        c.drawString(left_margin, current_y, f"Receipt No. {receipt_no}")
        
        date_text = f"Date: {self.donor_data.get('date', '')}"
        date_width = c.stringWidth(date_text, FONT_NORMAL, 11)
        c.drawString(right_margin - date_width, current_y, date_text)
        
        # Title
        current_y -= 40
        c.setFont(FONT_HEADING, 14)
        title = "DONATION RECEIPT"
        title_width = c.stringWidth(title, FONT_HEADING, 14)
        c.drawString((self.width - title_width) / 2, current_y, title)
        
        # Certification text
        current_y -= 35
        c.setFont(FONT_NORMAL, 11)
        cert_text = f"This is to certify that {self.org_settings['name']} has received a donation as per the following details:"
        c.drawString(left_margin, current_y, cert_text)
        
        # Donation details table
        current_y -= 30
        data = [[
            'Date of Donation',
            'Donor Name',
            'PAN',
            'Amount (Rs.)',
            'Purpose',
            'Mode of Payment'
        ], [
            self.donor_data.get('date', ''),
            self.donor_data.get('name', ''),
            self.donor_data.get('pan', 'N/A'),
            f"{float(self.donor_data.get('amount', '0.0')):,.2f}",
            self.donor_data.get('purpose', ''),
            self.donor_data.get('payment_mode', '')
        ]]
        
        # Calculate column widths
        table_width = right_margin - left_margin
        col_widths = [
            table_width * 0.15,  # Date
            table_width * 0.25,  # Name
            table_width * 0.15,  # PAN
            table_width * 0.15,  # Amount
            table_width * 0.15,  # Purpose
            table_width * 0.15   # Payment Mode
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), FONT_NORMAL, 10),
            ('FONT', (0, 0), (-1, 0), FONT_BOLD, 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, 1), 'RIGHT'),  # Right align amount
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        table.wrapOn(c, table_width, 50)
        table.drawOn(c, left_margin, current_y - 50)
        
        current_y -= 100  # Space for table
        
        # PAN declaration
        c.setFont(FONT_NORMAL, 11)
        pan_text = f"The Permanent Account Number (PAN) of {self.org_settings['name']} is {self.org_settings['pan_number']}."
        c.drawString(left_margin, current_y, pan_text)
        
        # Thank you message
        current_y -= 20
        c.drawString(left_margin, current_y, "We thank you for your kind consideration.")
        
        # Signature section
        current_y -= 40
        c.drawString(left_margin, current_y, "Sincerely,")
        current_y -= 20
        c.drawString(left_margin, current_y, f"For {self.org_settings['name']}")
        
        # Add signature if available
        try:
            signature_path = "assets/signature.png"
            if os.path.exists(signature_path):
                current_y -= 60
                sig_width = 1.5 * inch
                sig_height = 0.75 * inch
                c.drawImage(signature_path, left_margin, current_y, 
                          width=sig_width, height=sig_height, preserveAspectRatio=True)
        except:
            current_y -= 40
        
        # Signatory details
        current_y -= 25
        c.setFont(FONT_BOLD, 11)
        c.drawString(left_margin, current_y, self.org_settings.get('signature_holder', {}).get('name', ''))
        current_y -= 15
        c.drawString(left_margin, current_y, self.org_settings.get('signature_holder', {}).get('designation', ''))
        
        c.save()

def generate_receipt(donor_data, output_path):
    """Generate a donation receipt PDF"""
    # Load organization settings
    try:
        with open('config/settings.json', 'r') as f:
            settings = json.load(f)
            org_settings = settings.get('organization', {})
            
            # Ensure signature holder info is included
            if 'signature_holder' not in org_settings:
                org_settings['signature_holder'] = DEFAULT_RECEIPT_SETTINGS['signature_holder']
                
            if not org_settings:
                org_settings = DEFAULT_RECEIPT_SETTINGS
    except:
        org_settings = DEFAULT_RECEIPT_SETTINGS
    
    # Create receipt
    receipt = DonationReceipt(donor_data, org_settings)
    receipt.generate(output_path)

def pdf_settings_page():
    st.markdown("## 📄 PDF Template Settings")
    
    # File upload section
    st.markdown("### 📁 Upload Assets")
    
    # Logo upload
    st.markdown("#### Organization Logo")
    logo_col1, logo_col2 = st.columns([2, 1])
    with logo_col1:
        uploaded_logo = st.file_uploader("Upload your organization logo (PNG or JPG)", type=['png', 'jpg', 'jpeg'])
        if uploaded_logo:
            try:
                # Save the uploaded logo
                logo_image = Image.open(uploaded_logo)
                os.makedirs("assets", exist_ok=True)
                logo_image.save("assets/logo.png")
                st.success("✅ Logo uploaded successfully!")
            except Exception as e:
                st.error(f"❌ Failed to save logo: {str(e)}")
    with logo_col2:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", caption="Current Logo", width=150)
    
    # Signature upload
    st.markdown("#### Digital Signature")
    sig_col1, sig_col2 = st.columns([2, 1])
    with sig_col1:
        uploaded_signature = st.file_uploader("Upload your digital signature (PNG with transparent background)", type=['png'])
        if uploaded_signature:
            try:
                # Save the uploaded signature
                sig_image = Image.open(uploaded_signature)
                os.makedirs("assets", exist_ok=True)
                sig_image.save("assets/signature.png")
                st.success("✅ Signature uploaded successfully!")
            except Exception as e:
                st.error(f"❌ Failed to save signature: {str(e)}")
    with sig_col2:
        if os.path.exists("assets/signature.png"):
            st.image("assets/signature.png", caption="Current Signature", width=150)

    # Preview section
    st.markdown("### 👀 Receipt Preview")
    st.markdown("This is how your donation receipt will look with the current settings.")
    
    # Load organization settings
    try:
        with open('config/settings.json', 'r') as f:
            settings = json.load(f)
            org_settings = settings.get('organization', {})
    except:
        org_settings = {}
    
    if org_settings:
        # Create a sample receipt for preview
        sample_data = {
            "name": "John Doe",
            "amount": "10000",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "receipt_number": "PREVIEW/2024/001",
            "purpose": "General Fund",
            "payment_mode": "Bank Transfer",
            "pan": "ABCDE1234F"
        }
        
        # Generate preview receipt
        preview_path = "assets/receipt_preview.pdf"
        try:
            receipt = DonationReceipt(sample_data, org_settings)
            receipt.generate(preview_path)
            
            # Convert first page of PDF to image for preview
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(preview_path)
                page = doc[0]
                zoom = 2  # Increase zoom for better quality
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                preview_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Save and display preview image
                preview_image_path = "assets/receipt_preview.png"
                preview_image.save(preview_image_path, quality=95, dpi=(300, 300))
                
                # Zoom control
                zoom_level = st.slider("Zoom", min_value=50, max_value=150, value=100, step=10, format="%d%%")
                display_width = int(preview_image.width * (zoom_level / 100))
                st.image(preview_image_path, width=display_width)
                
                # Clean up
                doc.close()
                os.remove(preview_path)
            except ImportError:
                st.info("📝 Preview not available. Install PyMuPDF for preview functionality.")
        except Exception as e:
            st.error(f"❌ Failed to generate preview: {str(e)}")
    else:
        st.warning("⚠️ Please configure your organization details in Settings > General Information to see the receipt preview.") 