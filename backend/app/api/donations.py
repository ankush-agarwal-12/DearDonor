from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import re
import requests
from app.db.session import get_db
from app.schemas.donation import DonationResponse, DonationCreate, DonationUpdate
from app.models.donation import Donation
from app.core.security import get_current_org

router = APIRouter(prefix="/donations", tags=["Donations"])

def generate_receipt_number(org_id: str, request: Request) -> str:
    """Generate receipt number using the settings API"""
    try:
        # Get receipt format from settings API
        base_url = str(request.base_url).rstrip('/')
        headers = {"Authorization": request.headers.get("authorization", "")}
        
        response = requests.get(f"{base_url}/settings/receipt_format", headers=headers)
        
        if response.status_code == 200:
            receipt_format = response.json()
        else:
            # Default receipt format if not found
            receipt_format = {
                "format": "{prefix}/{YY}/{MM}/{XXX}",
                "prefix": "REC", 
                "next_sequence": 1
            }
        
        current_date = datetime.now()
        year_short = str(current_date.year)[-2:]
        month = str(current_date.month).zfill(2)
        
        # Generate receipt number
        sequence = receipt_format.get('next_sequence', 1)
        receipt_number = receipt_format['format'].format(
            prefix=receipt_format['prefix'],
            YY=year_short,
            MM=month,
            XXX=str(sequence).zfill(3)
        )
        
        # Update the next sequence in settings
        updated_format = receipt_format.copy()
        updated_format['next_sequence'] = sequence + 1
        
        update_response = requests.put(
            f"{base_url}/settings/receipt_format",
            json=updated_format,
            headers=headers
        )
        
        if update_response.status_code != 200:
            print(f"Warning: Failed to update receipt sequence. Status: {update_response.status_code}, Response: {update_response.text}")
        
        return receipt_number
    except Exception as e:
        print(f"Error generating receipt number: {str(e)}")
        # Fallback receipt number
        current_date = datetime.now()
        year_short = str(current_date.year)[-2:]
        month = str(current_date.month).zfill(2)
        return f"REC/{year_short}/{month}/001"

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
    request: Request = None,
):
    if not request:
        raise HTTPException(status_code=500, detail="Request object not available")
    
    # Generate receipt number using settings API
    receipt_number = generate_receipt_number(org_id, request)
    
    # Ensure payment_details is always a dict
    payment_details = data.payment_details if data.payment_details is not None else {}
    
    donation = Donation(
        organization_id=org_id,
        donor_id=data.donor_id,
        amount=data.amount,
        date=data.date,
        purpose=data.purpose,
        payment_mode=data.payment_mode,
        payment_details=payment_details,
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
    # Only update allowed fields
    allowed_fields = ["amount", "date", "purpose", "payment_mode", "payment_details"]
    update_data = {field: value for field, value in data.dict(exclude_unset=True).items() if field in allowed_fields}
    if "payment_details" in update_data and update_data["payment_details"] is None:
        update_data["payment_details"] = {}
    for field, value in update_data.items():
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