import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.donation import Donation
from app.models.donor import Donor
from app.core.security import get_current_org
from modules.pdf_template import generate_receipt, generate_receipt_bytes
from modules.supabase_utils import get_organization_settings, get_organization_receipt_number, get_organization_receipt_path
from datetime import datetime
from io import BytesIO

router = APIRouter(prefix="/receipts", tags=["Receipts"])

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
    donor_data = {
        "name": donor.full_name,
        "amount": float(donation.amount),
        "date": donation.date.strftime("%Y-%m-%d") if hasattr(donation.date, 'strftime') else str(donation.date),
        "receipt_number": receipt_number,
        "purpose": donation.purpose,
        "payment_mode": donation.payment_mode,
        "pan": donor.pan or "N/A"
    }
    pdf_bytes = generate_receipt_bytes(donor_data, organization_id=org_id)
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={safe_receipt_number}.pdf"
    }) 