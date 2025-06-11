import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from .email_template import get_template, get_subject
from datetime import datetime
import json
from num2words import num2words
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

def load_org_settings():
    """Load organization settings from config file"""
    try:
        with open('config/settings.json', 'r') as f:
            settings = json.load(f)
            org = settings.get('organization', {})
            
            # Get social media links
            social_media = org.get('social_media', {})
            social_links = []
            
            if social_media.get('facebook'):
                social_links.append(f'<a href="{social_media["facebook"]}">Facebook</a>')
            if social_media.get('instagram'):
                social_links.append(f'<a href="{social_media["instagram"]}">Instagram</a>')
            if social_media.get('youtube'):
                social_links.append(f'<a href="{social_media["youtube"]}">YouTube</a>')
                
            social_text = " | ".join(social_links) if social_links else "Follow us on social media"
            
            return {
                'name': org.get('name', 'Your Organization Name'),
                'department': 'Accounts Department',
                'email': org.get('email', 'your-email@gmail.com'),
                'phone': org.get('phone', '+91 1234567890'),
                'website': org.get('website', 'www.example.com'),
                'registration_number': org.get('registration_number', ''),
                'pan_number': org.get('pan_number', ''),
                'csr_number': org.get('csr_number', ''),
                'tax_exemption_number': org.get('tax_exemption_number', ''),
                'office_address': org.get('office_address', ''),
                'social': social_text
            }
    except Exception as e:
        print(f"Error loading organization settings: {str(e)}")
        return {
            'name': os.getenv("ORG_NAME", "Your Organization Name"),
            'department': 'Accounts Department',
            'email': os.getenv("ORG_EMAIL", "your-email@gmail.com"),
            'phone': os.getenv("ORG_PHONE", "+91 1234567890"),
            'website': os.getenv("ORG_WEBSITE", "www.example.com"),
            'registration_number': os.getenv("ORG_REG_NO", ""),
            'pan_number': os.getenv("ORG_PAN", ""),
            'csr_number': os.getenv("ORG_CSR", ""),
            'tax_exemption_number': os.getenv("ORG_TAX_EXEMPT", ""),
            'office_address': os.getenv("ORG_ADDRESS", ""),
            'social': "Follow us on social media"
        }

# Get organization details - reload on each use to get latest settings
def get_org_details():
    return load_org_settings()

# Email settings
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")

def convert_to_html(text, org_details):
    """Convert plain text email to HTML with proper formatting"""
    # Replace newlines with <br> tags
    html = text.replace('\n', '<br>')
    
    # Make email and phone clickable
    if org_details['email']:
        html = html.replace(org_details['email'], f'<a href="mailto:{org_details["email"]}">{org_details["email"]}</a>')
    if org_details['phone']:
        html = html.replace(org_details['phone'], f'<a href="tel:{org_details["phone"]}">{org_details["phone"]}</a>')
    
    # Add basic styling
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            a {{
                color: #2196F3;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
            {html}
    </body>
    </html>
    """
    
    return html

def get_template():
    """Get the email template from file"""
    try:
        with open('config/email_template.txt', 'r') as f:
            return f.read().strip()
    except:
        return """Dear {{Name}},

Thank you for your generous donation of Rs. {{Amount}} /- ({{AmountInWords}}) to {{orgName}}. Your contribution will help us make a difference in the lives of stray animals.

Receipt Details:
- Receipt Number: {{receiptNumber}}
- Date: {{Date}}
- Purpose: {{Purpose}}
- Payment Mode: {{PaymentMode}}

The official receipt is attached to this email.

Best regards,
{{orgDepartment}}
{{orgName}}

Contact us:
{{orgEmail}} | {{orgPhone}}
{{orgSocial}}"""

def get_subject():
    """Get the email subject from file"""
    try:
        with open('config/email_subject.txt', 'r') as f:
            return f.read().strip()
    except:
        return "Donation Receipt - Thank You, {{Name}}"

def save_template(template, subject):
    """Save the email template and subject to file"""
    os.makedirs('config', exist_ok=True)
    
    with open('config/email_template.txt', 'w') as f:
        f.write(template)
    
    with open('config/email_subject.txt', 'w') as f:
        f.write(subject)

def send_email_receipt(to_email, donor_name, receipt_path, amount, receipt_number="", purpose="", payment_mode=""):
    """Send donation receipt email using the template"""
    try:
        # Get latest organization details
        org_details = get_org_details()
        
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
    
        # Get and format subject line
        subject_template = get_subject()
        subject = subject_template.replace("{{Name}}", donor_name)
        msg['Subject'] = subject

        # Get the template and format it with all placeholders
        template = get_template()
        
        # Convert amount to words
        try:
            amount_in_words = num2words(float(amount), lang='en_IN').title()
        except:
            amount_in_words = str(amount)
        
        # Format the template with proper line breaks
        email_body = template.replace("{{Name}}", donor_name)\
                            .replace("{{Amount}}", str(amount))\
                            .replace("{{AmountInWords}}", amount_in_words)\
                            .replace("{{Date}}", datetime.now().strftime("%d/%m/%Y"))\
                            .replace("{{receiptNumber}}", receipt_number)\
                            .replace("{{Purpose}}", purpose or "General Donation")\
                            .replace("{{PaymentMode}}", payment_mode or "Online")\
                            .replace("{{orgName}}", org_details['name'])\
                            .replace("{{orgDepartment}}", org_details['department'])\
                            .replace("{{orgEmail}}", org_details['email'])\
                            .replace("{{orgPhone}}", org_details['phone'])\
                            .replace("{{orgSocial}}", org_details['social'])
        
        # Add plain text version
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # Add HTML version
        html_body = convert_to_html(email_body, org_details)
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Attach the PDF receipt
        with open(receipt_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(receipt_path)}"'
            )
            msg.attach(part)
        
        # Send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False