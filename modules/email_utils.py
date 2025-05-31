import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

# TODO: Replace with your actual Gmail address and App Password
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")

def send_email_receipt(to_email, donor_name, receipt_path):
    msg = EmailMessage()
    msg['Subject'] = f"Donation Receipt – Thank You, {donor_name}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    msg.set_content(f"""
Dear {donor_name},

Thank you for your generous donation. Please find the attached receipt.

Warm regards,  
The Stray Army Charitable Trust
""")

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