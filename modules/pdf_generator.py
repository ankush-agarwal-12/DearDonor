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
from .pdf_template import get_pdf_settings
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.settings = get_pdf_settings()
        self.width, self.height = A4
        
    def _setup_canvas(self, output_path):
        """Setup canvas with basic configurations"""
        c = canvas.Canvas(output_path, pagesize=A4)
        receipt_settings = self.settings['receipt']
        
        # Set font
        font_name = receipt_settings['font_family']
        if font_name in ['Helvetica', 'Times-Roman', 'Courier']:
            c.setFont(font_name, 12)
        
        return c
    
    def _draw_header(self, c, org_name, reg_no):
        """Draw the organization header"""
        receipt_settings = self.settings['receipt']
        
        # Draw logo
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            logo_width = 80
            if receipt_settings['logo_position'] == 'right':
                x = self.width - logo_width - 50
            elif receipt_settings['logo_position'] == 'center':
                x = (self.width - logo_width) / 2
            else:  # left
                x = 50
            c.drawImage(logo_path, x, self.height - 120, width=logo_width, height=80)
        
        # Draw organization name and registration
        c.setFont('Helvetica-Bold', 16)
        c.setFillColor(colors.HexColor(receipt_settings['header_color']))
        c.drawCentredString(self.width/2, self.height - 50, org_name)
        c.setFont('Helvetica', 10)
        c.drawCentredString(self.width/2, self.height - 70, f"Registered Under Indian Trusts Act, 1882. (Reg No. - {reg_no})")
    
    def generate_receipt(self, data, output_path):
        """Generate a donation receipt PDF"""
        c = self._setup_canvas(output_path)
        receipt_settings = self.settings['receipt']
        
        # Draw header
        self._draw_header(c, data['org_name'], data['reg_no'])
        
        # Draw border if enabled
        if receipt_settings['show_border']:
            c.setStrokeColor(colors.HexColor(receipt_settings['border_color']))
            c.rect(30, 30, self.width-60, self.height-60)
        
        # Receipt details
        c.setFont('Helvetica-Bold', 12)
        c.drawString(50, self.height - 150, f"Receipt No. - {data['receipt_no']}")
        
        # Draw office address
        c.setFont('Helvetica', 10)
        c.drawRightString(self.width - 50, self.height - 150, data['org_address'])
        
        # Donor details
        y = self.height - 200
        c.setFont('Helvetica', 12)
        fields = [
            ('Received with thanks from', data['donor_name']),
            ('Amount', f"Rs. {data['amount']} /-"),
            ('Amount (in words)', data['amount_words']),
            ('By cash / Draft / NEFT / RTGS / Cheque* No', data['payment_details']),
            ('Dated', data['date']),
            ('Towards', data['purpose']),
            ('Address', data['donor_address']),
            ('Contact No', data['donor_phone']),
            ('PAN No', data['donor_pan']),
            ('Email', data['donor_email'])
        ]
        
        for label, value in fields:
            c.setFont('Helvetica', 11)
            c.drawString(50, y, f"{label} - ")
            c.setFont('Helvetica-Bold', 11)
            c.drawString(200, y, value)
            y -= 25
        
        # Draw signature if enabled
        if receipt_settings['include_signature']:
            signature_path = "assets/signature.png"
            if os.path.exists(signature_path):
                c.drawImage(signature_path, self.width - 150, 100, width=100, height=50)
            c.setFont('Helvetica', 10)
            c.drawCentredString(self.width - 100, 80, "(Authorised Signatory)")
        
        # Draw footer
        c.setFont('Helvetica', 8)
        c.drawString(50, 50, receipt_settings['footer_text'])
        
        c.save()
        
        # Generate thank you note if enabled
        if self.settings['enable_thankyou']:
            self.generate_thankyou_note(data, output_path.replace('.pdf', '_thankyou.pdf'))
    
    def generate_thankyou_note(self, data, output_path):
        """Generate a thank you note PDF"""
        c = self._setup_canvas(output_path)
        thankyou_settings = self.settings['thankyou']
        
        # Draw decorative elements based on theme
        if thankyou_settings['theme'] == 'butterflies':
            # Draw butterflies and decorative elements
            butterfly_paths = [
                "assets/butterfly1.png",
                "assets/butterfly2.png"
            ]
            for path in butterfly_paths:
                if os.path.exists(path):
                    c.drawImage(path, 50, self.height - 150, width=30, height=30)
                    c.drawImage(path, self.width - 80, self.height - 150, width=30, height=30)
        
        # Draw organization logo if enabled
        if thankyou_settings['show_logo']:
            logo_path = "assets/logo.png"
            if os.path.exists(logo_path):
                c.drawImage(logo_path, self.width - 100, self.height - 100, width=60, height=60)
        
        # Draw thank you message
        c.setFont('Helvetica-Bold', 24)
        c.drawCentredString(self.width/2, self.height - 150, "Thank You")
        
        # Draw personalized message
        message = f"""Dear {data['donor_name']},

We are immensely grateful for your generous contribution to {data['org_name']}. Your support is not only appreciated but vital to our mission, we couldn't be more thankful.

We haven't lost hope, just because of kind people like you...

Warm regards,"""
        
        # Draw message with proper formatting
        y = self.height - 250
        for line in message.split('\n'):
            c.setFont('Helvetica', 12)
            c.drawString(100, y, line)
            y -= 20
        
        # Draw signature if enabled
        if thankyou_settings['include_signature']:
            signature_path = "assets/signature.png"
            if os.path.exists(signature_path):
                c.drawImage(signature_path, 100, y - 50, width=100, height=50)
            c.setFont('Helvetica', 10)
            c.drawString(100, y - 70, f"(Co-Founder, {data['org_name']})")
        
        c.save()

# Function to format currency in words
def number_to_words(number):
    """Convert number to words for Indian currency"""
    # Implementation of number to words conversion
    # This is a placeholder - you would need to implement the actual conversion
    return f"Rupees {number} Only" 