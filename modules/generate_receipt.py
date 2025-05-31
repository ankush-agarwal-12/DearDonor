from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def generate_receipt(donor_name, amount, date, purpose, mode, receipt_path):
    c = canvas.Canvas(receipt_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, 10 * inch, "Donation Receipt")
    
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, 9.5 * inch, f"Donor Name: {donor_name}")
    c.drawString(1 * inch, 9.2 * inch, f"Amount: ₹{amount}")
    c.drawString(1 * inch, 8.9 * inch, f"Date: {date}")
    c.drawString(1 * inch, 8.6 * inch, f"Purpose: {purpose}")
    c.drawString(1 * inch, 8.3 * inch, f"Mode of Payment: {mode}")
    c.drawString(1 * inch, 7.8 * inch, "Thank you for your generous contribution!")
    
    c.save()
    return receipt_path