import os
import sys
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.donation import Donation
from app.models.donor import Donor
from app.core.security import get_current_org
from modules.supabase_utils import get_organization_settings, get_organization_receipt_path
from datetime import datetime
from io import BytesIO

# Add the template_generate directory to the Python path
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template_generate')
sys.path.insert(0, template_dir)

try:
    from template_generate.render import generate_receipt_pdf
except ImportError as e:
    print(f"Warning: Could not import template system: {e}")
    # Fallback to old system
    from modules.pdf_template import generate_receipt_bytes

router = APIRouter(prefix="/receipts", tags=["Receipts"])

def get_payment_details_display(payment_details, payment_mode):
    """Extract and format payment details for receipt display"""
    try:
        if not payment_details or payment_details == {}:
            return "N/A"
        
        if isinstance(payment_details, dict):
            # Try to extract meaningful payment info based on payment mode
            if payment_mode and payment_mode.lower() in ['upi', 'online', 'digital']:
                # For digital payments, look for transaction ID, UPI ID, etc.
                for key in ['transaction_id', 'txn_id', 'upi_id', 'ref_number', 'reference']:
                    if key in payment_details:
                        return str(payment_details[key])
            elif payment_mode and payment_mode.lower() in ['cheque', 'check']:
                # For cheques, look for cheque number
                for key in ['cheque_number', 'check_number', 'cheque_no']:
                    if key in payment_details:
                        return f"Cheque No: {payment_details[key]}"
            elif payment_mode and payment_mode.lower() in ['neft', 'rtgs', 'bank_transfer']:
                # For bank transfers, look for reference number
                for key in ['reference_number', 'ref_no', 'transaction_id']:
                    if key in payment_details:
                        return str(payment_details[key])
            
            # If no specific field found, return first non-empty value
            for value in payment_details.values():
                if value and str(value).strip():
                    return str(value)
        
        # Fallback: convert to string
        return str(payment_details) if payment_details else "N/A"
        
    except Exception as e:
        print(f"Error processing payment details: {e}")
        return "N/A"

@router.get("/{donation_id}")
def get_receipt(donation_id: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    # Get donation
    donation = db.query(Donation).filter(Donation.organization_id == org_id, Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    # Get donor
    donor = db.query(Donor).filter(Donor.id == donation.donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    # Get org settings
    org_settings = get_organization_settings(org_id)
    
    # Use the stored receipt_number
    receipt_number = donation.receipt_number
    if not receipt_number:
        raise HTTPException(status_code=500, detail="No receipt number found for this donation")
    
    # Use a safe filename
    safe_receipt_number = receipt_number.replace('/', '_')
    
    try:
        # Prepare data for new template system
        donor_data = {
            "name": donor.full_name,
            "address": donor.address or "Address Not Provided",
            "phone": donor.phone or "Phone Not Provided", 
            "email": donor.email or "Email Not Provided",
            "pan": donor.pan or "N/A"
        }
        
        org_data = org_settings.get('organization', {})
        
        donation_data = {
            "receipt_number": receipt_number,
            "amount": float(donation.amount),
            "date": donation.date.strftime("%Y-%m-%d") if hasattr(donation.date, 'strftime') else str(donation.date),
            "purpose": donation.purpose or "General Fund",
            "payment_mode": donation.payment_mode or "Online",
            "payment_details": get_payment_details_display(donation.payment_details, donation.payment_mode)
        }
        
        # Determine donor type - check for Company/Individual
        donor_type = getattr(donor, 'donor_type', 'Individual')
        print(f"Debug: Generating receipt for donor type: {donor_type}")
        
        # Generate PDF using new template system
        pdf_bytes = generate_receipt_pdf(donor_data, org_data, donation_data, donor_type, organization_id=org_id)
        
        return StreamingResponse(
            BytesIO(pdf_bytes), 
            media_type="application/pdf", 
            headers={
                "Content-Disposition": f"attachment; filename={safe_receipt_number}.pdf"
            }
        )
        
    except Exception as e:
        print(f"Error generating receipt with new template system: {str(e)}")
        print(f"Falling back to old system...")
        
        # Fallback to old system
        donor_data_old = {
            "name": donor.full_name,
            "amount": float(donation.amount),
            "date": donation.date.strftime("%Y-%m-%d") if hasattr(donation.date, 'strftime') else str(donation.date),
            "receipt_number": receipt_number,
            "purpose": donation.purpose,
            "payment_mode": donation.payment_mode,
            "pan": donor.pan or "N/A"
        }
        pdf_bytes = generate_receipt_bytes(donor_data_old, organization_id=org_id)
        
        return StreamingResponse(
            BytesIO(pdf_bytes), 
            media_type="application/pdf", 
            headers={
                "Content-Disposition": f"attachment; filename={safe_receipt_number}.pdf"
            }
        ) 