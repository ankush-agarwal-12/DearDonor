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
from .supabase_utils import get_organization_settings

load_dotenv()

# Fallback email configuration from environment (for backward compatibility)
FALLBACK_EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@gmail.com")
FALLBACK_EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
FALLBACK_SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
FALLBACK_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

def get_email_config(organization_id=None):
    """Get email configuration for organization"""
    if organization_id:
        try:
            org_settings = get_organization_settings(organization_id)
            email_config = org_settings.get('email_config', {})
            
            # Return config if properly configured
            if email_config.get('email_address') and email_config.get('email_password'):
                return {
                    'email_address': email_config.get('email_address'),
                    'email_password': email_config.get('email_password'),
                    'smtp_server': email_config.get('smtp_server', 'smtp.gmail.com'),
                    'smtp_port': email_config.get('smtp_port', 587),
                    'use_tls': email_config.get('use_tls', True)
                }
        except Exception as e:
            print(f"Error getting organization email config: {e}")
    
    # Fallback to environment variables
    return {
        'email_address': FALLBACK_EMAIL_ADDRESS,
        'email_password': FALLBACK_EMAIL_PASSWORD,
        'smtp_server': FALLBACK_SMTP_SERVER,
        'smtp_port': FALLBACK_SMTP_PORT,
        'use_tls': True
    }

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
            'name': 'Your Organization Name',
            'department': 'Accounts Department',
            'email': 'your-email@gmail.com',
            'phone': '+91 1234567890',
            'website': 'www.example.com',
            'registration_number': '',
            'pan_number': '',
            'csr_number': '',
            'tax_exemption_number': '',
            'office_address': '',
            'social': 'Follow us on social media'
        }

def get_org_details():
    """Legacy function for backward compatibility"""
    return load_org_settings()

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
        return "Thank you for your donation - {{Name}}"

def save_email_template(template):
    """Save email template content to file"""
    with open('config/email_template.txt', 'w') as f:
        f.write(template)

def load_email_template():
    """Load email template from file"""
    try:
        with open('config/email_template.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
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

def save_email_subject(subject):
    """Save email subject template to file"""
    with open('config/email_subject.txt', 'w') as f:
        f.write(subject)

def load_email_subject():
    """Load email subject template from file"""
    try:
        with open('config/email_subject.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Thank you for your donation - {{Name}}"

def send_email_receipt(to_email, donor_name, receipt_path, amount, receipt_number="", purpose="", payment_mode="", org_details=None, donation_date=None, organization_id=None, **kwargs):
    """Send donation receipt email using the template. Accepts org_details dict for organization info."""
    try:
        # Get email configuration for the organization
        email_config = get_email_config(organization_id)
        
        # Use provided org_details or fallback to legacy config
        if org_details is None:
            org_details = get_org_details()
        # Compose social links for email footer
        social_links = []
        social_media = org_details.get('social_media', {})
        if social_media.get('facebook'):
            social_links.append(f'<a href="{social_media["facebook"]}">Facebook</a>')
        if social_media.get('instagram'):
            social_links.append(f'<a href="{social_media["instagram"]}">Instagram</a>')
        if social_media.get('youtube'):
            social_links.append(f'<a href="{social_media["youtube"]}">YouTube</a>')
        social_text = " | ".join(social_links) if social_links else "Follow us on social media"
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['From'] = email_config['email_address']
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
        
        # Use provided donation_date or fall back to today's date
        if donation_date:
            formatted_date = donation_date  # Already formatted as DD/MM/YYYY from calling function
        else:
            formatted_date = datetime.now().strftime("%d/%m/%Y")
            
        # Format the template with proper line breaks
        email_body = template.replace("{{Name}}", donor_name)\
                            .replace("{{Amount}}", str(amount))\
                            .replace("{{AmountInWords}}", amount_in_words)\
                            .replace("{{Date}}", formatted_date)\
                            .replace("{{receiptNumber}}", receipt_number)\
                            .replace("{{Purpose}}", purpose or "General Donation")\
                            .replace("{{PaymentMode}}", payment_mode or "Online")\
                            .replace("{{orgName}}", org_details.get('name', ''))\
                            .replace("{{orgDepartment}}", org_details.get('department', 'Accounts Department'))\
                            .replace("{{orgEmail}}", org_details.get('email', ''))\
                            .replace("{{orgPhone}}", org_details.get('phone', ''))\
                            .replace("{{orgSocial}}", social_text)
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
        
        # Send the email using organization-specific SMTP settings
        print(f"Sending email from {email_config['email_address']} via {email_config['smtp_server']}:{email_config['smtp_port']}")
        
        if email_config['use_tls']:
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as smtp:
                smtp.starttls()
                smtp.login(email_config['email_address'], email_config['email_password'])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(email_config['smtp_server'], email_config['smtp_port']) as smtp:
                smtp.login(email_config['email_address'], email_config['email_password'])
                smtp.send_message(msg)
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False