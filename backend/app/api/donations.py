from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.schemas.donation import DonationResponse, DonationCreate, DonationUpdate
from app.models.donation import Donation
from app.core.security import get_current_org
from modules.supabase_utils import get_organization_receipt_number

router = APIRouter(prefix="/donations", tags=["Donations"])

@router.get("/", response_model=List[DonationResponse])
def list_donations(
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
    donor_id: Optional[UUID] = Query(None),
    purpose: Optional[str] = Query(None),
):
    query = db.query(Donation).filter(Donation.organization_id == org_id)
    if donor_id:
        query = query.filter(Donation.donor_id == donor_id)
    if purpose:
        query = query.filter(Donation.purpose.ilike(f"%{purpose}%"))
    donations = query.order_by(Donation.date.desc()).all()
    return donations

@router.post("/", response_model=DonationResponse, status_code=201)
def add_donation(
    data: DonationCreate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    # Generate and store receipt number at creation time
    receipt_number = get_organization_receipt_number(org_id)
    donation = Donation(
        organization_id=org_id,
        donor_id=data.donor_id,
        amount=data.amount,
        date=data.date,
        purpose=data.purpose,
        payment_mode=data.payment_mode,
        payment_details=data.payment_details,
        receipt_path=data.receipt_path,
        receipt_number=receipt_number,
        email_sent=data.email_sent,
        whatsapp_sent=data.whatsapp_sent,
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation

@router.get("/{donation_id}", response_model=DonationResponse)
def get_donation(
    donation_id: UUID,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    donation = db.query(Donation).filter(Donation.organization_id == org_id, Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation

@router.put("/{donation_id}", response_model=DonationResponse)
def update_donation(
    donation_id: UUID,
    data: DonationUpdate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    donation = db.query(Donation).filter(Donation.organization_id == org_id, Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(donation, field, value)
    db.commit()
    db.refresh(donation)
    return donation

@router.delete("/{donation_id}", status_code=204)
def delete_donation(
    donation_id: UUID,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    donation = db.query(Donation).filter(Donation.organization_id == org_id, Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    db.delete(donation)
    db.commit()
    return 