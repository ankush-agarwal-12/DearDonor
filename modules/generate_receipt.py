print("🔄 LOADING generate_receipt.py")
import pdfkit
import os

def generate_receipt(donor_name, amount, date, purpose, mode, receipt_path):
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ font-size: 24px; font-weight: bold; }}
            .section {{ margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">Donation Receipt</div>
        <div class="section"><strong>Donor Name:</strong> {donor_name}</div>
        <div class="section"><strong>Amount:</strong> ₹{amount}</div>
        <div class="section"><strong>Date:</strong> {date}</div>
        <div class="section"><strong>Purpose:</strong> {purpose}</div>
        <div class="section"><strong>Mode of Payment:</strong> {mode}</div>
        <div class="section" style="margin-top:40px;">Thank you for your generous contribution!</div>
    </body>
    </html>
    """
    # Path to wkhtmltopdf if needed
    try:
        config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
    except Exception:
        config = None
    # Convert to PDF
    if config:
        pdfkit.from_string(html_content, receipt_path, configuration=config)
    else:
        pdfkit.from_string(html_content, receipt_path)
    return receipt_path
