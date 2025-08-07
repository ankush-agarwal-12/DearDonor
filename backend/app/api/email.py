import os
import sys
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.donation import Donation
from app.models.donor import Donor
from app.models.email_template import OrganizationEmailTemplate
from app.schemas.email_template import OrganizationEmailTemplateCreate, OrganizationEmailTemplateUpdate, OrganizationEmailTemplateResponse
from app.core.security import get_current_org
from fastapi.responses import JSONResponse
from modules.supabase_utils import get_organization_settings, get_organization_receipt_path
from modules.email_utils import send_email_receipt
from datetime import datetime
from typing import List

# Add the template_generate directory to the Python path
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template_generate')
sys.path.insert(0, template_dir)

try:
    from template_generate.render import generate_receipt_pdf
except ImportError as e:
    print(f"Warning: Could not import new template system: {e}")
    # Fallback to old system
    from modules.pdf_template import generate_receipt

# Helper function for payment details (same as in receipts.py)
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

# Email template management endpoints (moved to /email-templates)
email_templates_router = APIRouter(prefix="/email-templates", tags=["EmailTemplates"])

@email_templates_router.get("/", response_model=List[OrganizationEmailTemplateResponse])
def get_email_templates(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    """Get all email templates for the organization"""
    templates = db.query(OrganizationEmailTemplate).filter(
        OrganizationEmailTemplate.organization_id == org_id
    ).all()
    return templates

@email_templates_router.post("/", response_model=OrganizationEmailTemplateResponse)
def create_email_template(
    template: OrganizationEmailTemplateCreate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org)
):
    """Create a new email template"""
    new_template = OrganizationEmailTemplate(
        organization_id=org_id,
        template_type=template.template_type,
        content=template.content,
        is_active=template.is_active
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

@email_templates_router.put("/{template_id}", response_model=OrganizationEmailTemplateResponse)
def update_email_template(
    template_id: str,
    template: OrganizationEmailTemplateUpdate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org)
):
    """Update an email template"""
    db_template = db.query(OrganizationEmailTemplate).filter(
        OrganizationEmailTemplate.organization_id == org_id,
        OrganizationEmailTemplate.id == template_id
    ).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Email template not found")
    
    for field, value in template.dict(exclude_unset=True).items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

@email_templates_router.delete("/{template_id}")
def delete_email_template(
    template_id: str,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org)
):
    """Delete an email template"""
    db_template = db.query(OrganizationEmailTemplate).filter(
        OrganizationEmailTemplate.organization_id == org_id,
        OrganizationEmailTemplate.id == template_id
    ).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Email template not found")
    
    db.delete(db_template)
    db.commit()
    return {"detail": "Email template deleted successfully"}

# Only /receipts/{donation_id}/email remains in the /receipts router
from app.models.organization import Organization
receipts_email_router = APIRouter(prefix="/receipts", tags=["Email"])

@receipts_email_router.post("/{donation_id}/email")
def send_receipt_email(donation_id: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    donation = db.query(Donation).filter(Donation.organization_id == org_id, Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    donor = db.query(Donor).filter(Donor.id == donation.donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org_settings = get_organization_settings(org_id)
    org_details = org_settings.get('organization', {})
    receipt_number = donation.receipt_number
    if not receipt_number:
        raise HTTPException(status_code=500, detail="No receipt number found for this donation")
    
    safe_receipt_number = receipt_number.replace('/', '_')
    
    try:
        # Use new template system
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
        print(f"Debug: Generating email receipt for donor type: {donor_type}")
        
        # Generate PDF using new template system
        pdf_bytes = generate_receipt_pdf(donor_data, org_data, donation_data, donor_type, organization_id=org_id)
        
        # Save to temporary file
        import tempfile
        temp_dir = tempfile.gettempdir()
        receipt_path = os.path.join(temp_dir, f"{safe_receipt_number}.pdf")
        
        with open(receipt_path, 'wb') as f:
            f.write(pdf_bytes)
            
        print(f"✅ Generated receipt PDF at: {receipt_path}")
        
    except Exception as e:
        print(f"Error generating receipt with new template system: {str(e)}")
        print(f"Falling back to old system...")
        
        # Fallback to old system
        import tempfile
        temp_dir = tempfile.gettempdir()
        receipt_path = os.path.join(temp_dir, f"{safe_receipt_number}.pdf")
        
        donor_data_old = {
            "name": donor.full_name,
            "amount": float(donation.amount),
            "date": donation.date.strftime("%Y-%m-%d") if hasattr(donation.date, 'strftime') else str(donation.date),
            "receipt_number": receipt_number,
            "purpose": donation.purpose,
            "payment_mode": donation.payment_mode,
            "pan": donor.pan or "N/A"
        }
        
        if not os.path.exists(receipt_path):
            generate_receipt(donor_data_old, receipt_path, organization_id=org_id)
    
    if not os.path.exists(receipt_path):
        raise HTTPException(status_code=500, detail="Failed to generate receipt PDF")
    
    # Format donation date for email (DD/MM/YYYY format)
    donation_date_formatted = donation.date.strftime("%d/%m/%Y") if hasattr(donation.date, 'strftime') else str(donation.date)
    
    # Validate SMTP configuration before proceeding
    from modules.email_utils import get_email_config, validate_email_config
    email_config = get_email_config(org_id)
    error_msg = validate_email_config(email_config)
    if error_msg:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Use organization details from database for email
    email_sent = send_email_receipt(
        to_email=donor.email,
        donor_name=donor.full_name,
        receipt_path=receipt_path,
        amount=float(donation.amount),
        receipt_number=receipt_number,
        purpose=donation.purpose,
        payment_mode=donation.payment_mode,
        org_details=org_details,
        donation_date=donation_date_formatted,  # Pass the actual donation date
        organization_id=org_id  # Pass organization ID for email config
    )
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send email receipt")
    
    # Update donation to mark email as sent
    donation.email_sent = True
    db.commit()
    
    return JSONResponse(content={"detail": "Email sent successfully!"}) 