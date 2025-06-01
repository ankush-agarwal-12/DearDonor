import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from .email_template import get_template, get_subject
from datetime import datetime

load_dotenv()

# Get organization details from environment variables
ORG_NAME = os.getenv("ORG_NAME", "Your Organization Name")
ORG_DEPARTMENT = os.getenv("ORG_DEPARTMENT", "Accounts Department")
ORG_EMAIL = os.getenv("ORG_EMAIL", "your-email@gmail.com")
ORG_PHONE = os.getenv("ORG_PHONE", "+91 1234567890")
ORG_SOCIAL = os.getenv("ORG_SOCIAL", "YouTube | Instagram | Facebook")

# Email settings
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")

def convert_to_html(text):
    """Convert the template to proper HTML format"""
    # Replace newlines with HTML line breaks
    html = text.replace('\n', '<br>')
    return f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                small {{ color: #666; }}
            </style>
        </head>
        <body>
            {html}
        </body>
    </html>
    """

def send_email_receipt(to_email, donor_name, receipt_path, amount, receipt_number=""):
    msg = EmailMessage()
    
    # Get and format subject line
    subject_template = get_subject()
    subject = subject_template.replace("{{Name}}", donor_name)
    msg['Subject'] = subject
    
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    # Get the template and format it with all placeholders
    template = get_template()
    email_body = template.replace("{{Name}}", donor_name)\
                        .replace("{{Amount}}", str(amount))\
                        .replace("{{Date}}", datetime.now().strftime("%Y-%m-%d"))\
                        .replace("{{receiptNumber}}", receipt_number)\
                        .replace("{{orgName}}", ORG_NAME)\
                        .replace("{{orgDepartment}}", ORG_DEPARTMENT)\
                        .replace("{{orgEmail}}", ORG_EMAIL)\
                        .replace("{{orgPhone}}", ORG_PHONE)\
                        .replace("{{orgSocial}}", ORG_SOCIAL)
    
    # Set both HTML and plain text versions
    msg.set_content(email_body.replace('<br>', '\n')  # Plain text version
                             .replace('<b>', '').replace('</b>', '')
                             .replace('<i>', '').replace('</i>', '')
                             .replace('<u>', '').replace('</u>', '')
                             .replace('<small>', '').replace('</small>', ''))
    
    msg.add_alternative(convert_to_html(email_body), subtype='html')

    if os.path.exists(receipt_path):
        with open(receipt_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(receipt_path)
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)
    else:
        print(f"❌ PDF file not found at {receipt_path}")
        return False

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("✅ Email sent with attachment")
            return True
    except Exception as e:
        print("❌ Email sending failed:", e)
        return False