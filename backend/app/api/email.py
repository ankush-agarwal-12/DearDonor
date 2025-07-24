import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.donation import Donation
from app.models.donor import Donor
from app.models.email_template import OrganizationEmailTemplate
from app.schemas.email_template import OrganizationEmailTemplateCreate, OrganizationEmailTemplateUpdate, OrganizationEmailTemplateResponse
from app.core.security import get_current_org
from fastapi.responses import JSONResponse
from modules.pdf_template import generate_receipt
from modules.supabase_utils import get_organization_settings, get_organization_receipt_number, get_organization_receipt_path
from modules.email_utils import send_email_receipt
from datetime import datetime
from typing import List

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
    import tempfile
    temp_dir = tempfile.gettempdir()
    receipt_path = os.path.join(temp_dir, f"{safe_receipt_number}.pdf")
    donor_data = {
        "name": donor.full_name,
        "amount": float(donation.amount),
        "date": donation.date.strftime("%Y-%m-%d") if hasattr(donation.date, 'strftime') else str(donation.date),
        "receipt_number": receipt_number,
        "purpose": donation.purpose,
        "payment_mode": donation.payment_mode,
        "pan": donor.pan or "N/A"
    }
    if not os.path.exists(receipt_path):
        generate_receipt(donor_data, receipt_path, organization_id=org_id)
    if not os.path.exists(receipt_path):
        raise HTTPException(status_code=500, detail="Failed to generate receipt PDF")
    # Use organization details from database for email
    email_sent = send_email_receipt(
        to_email=donor.email,
        donor_name=donor.full_name,
        receipt_path=receipt_path,
        amount=donor_data["amount"],
        receipt_number=donor_data["receipt_number"],
        purpose=donor_data["purpose"],
        payment_mode=donor_data["payment_mode"],
        org_details=org_details
    )
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send email receipt")
    return JSONResponse(content={"detail": "Email sent successfully!"}) 