import smtplib
from email.message import EmailMessage
import os

def send_email_receipt(to_email, donor_name, receipt_path):
    msg = EmailMessage()
    msg['Subject'] = f"Donation Receipt – Thank You, {donor_name}"
    msg['From'] = "your-email@gmail.com"
    msg['To'] = to_email

    msg.set_content(f"""
Dear {donor_name},

Thank you for your generous donation. Please find the attached receipt.

Warm regards,  
The Stray Army Charitable Trust
""")

    # ✅ Make sure file exists and attach properly
    if os.path.exists(receipt_path):
        with open(receipt_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(receipt_path)
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)
    else:
        print(f"❌ PDF file not found at {receipt_path}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("your-email@gmail.com", "your-app-password")
            smtp.send_message(msg)
            print("✅ Email sent with attachment")
            return True
    except Exception as e:
        print("❌ Email sending failed:", e)
        return False
