from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def generate_receipt(donor_name, amount, date, purpose, mode, receipt_path, payment_details=None):
    c = canvas.Canvas(receipt_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, 10 * inch, "Donation Receipt")
    
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, 9.5 * inch, f"Donor Name: {donor_name}")
    c.drawString(1 * inch, 9.2 * inch, f"Amount: ₹{amount}")
    c.drawString(1 * inch, 8.9 * inch, f"Date: {date}")
    c.drawString(1 * inch, 8.6 * inch, f"Purpose: {purpose}")
    c.drawString(1 * inch, 8.3 * inch, f"Mode of Payment: {mode}")
    
    # Add payment details if available
    y_position = 8.0
    if payment_details:
        if mode == "Cheque" and payment_details.get("cheque_no") and payment_details.get("bank_name"):
            c.drawString(1 * inch, y_position * inch, f"Cheque Number: {payment_details['cheque_no']}")
            y_position -= 0.3
            c.drawString(1 * inch, y_position * inch, f"Bank Name: {payment_details['bank_name']}")
        elif mode in ["NEFT", "UPI"] and payment_details.get("transaction_id"):
            c.drawString(1 * inch, y_position * inch, f"Transaction ID: {payment_details['transaction_id']}")
    
    c.drawString(1 * inch, (y_position - 0.5) * inch, "Thank you for your generous contribution!")
    
    c.save()
    return receipt_path