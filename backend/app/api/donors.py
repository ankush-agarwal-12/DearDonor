from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.schemas.donor import DonorResponse, DonorCreate, DonorUpdate
from app.models.donor import Donor
from app.core.security import get_current_org

router = APIRouter(prefix="/donors", tags=["Donors"])

@router.get("/", response_model=List[DonorResponse])
def list_donors(
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
    search: Optional[str] = Query(None, description="Search by name or email"),
):
    query = db.query(Donor).filter(Donor.organization_id == org_id)
    if search:
        query = query.filter(
            (Donor.full_name.ilike(f"%{search}%")) |
            (Donor.email.ilike(f"%{search}%"))
        )
    donors = query.order_by(Donor.created_at.desc()).all()
    return donors

@router.post("/", response_model=DonorResponse, status_code=201)
def add_donor(
    data: DonorCreate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    existing = db.query(Donor).filter(Donor.organization_id == org_id, Donor.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Donor with this email already exists")
    donor = Donor(
        organization_id=org_id,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        address=data.address,
        pan=data.pan,
        donor_type=data.donor_type,
    )
    db.add(donor)
    db.commit()
    db.refresh(donor)
    return donor

@router.get("/{donor_id}", response_model=DonorResponse)
def get_donor(
    donor_id: UUID,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    donor = db.query(Donor).filter(Donor.organization_id == org_id, Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor

@router.put("/{donor_id}", response_model=DonorResponse)
def update_donor(
    donor_id: UUID,
    data: DonorUpdate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    donor = db.query(Donor).filter(Donor.organization_id == org_id, Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(donor, field, value)
    db.commit()
    db.refresh(donor)
    return donor

@router.delete("/{donor_id}", status_code=204)
def delete_donor(
    donor_id: UUID,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    donor = db.query(Donor).filter(Donor.organization_id == org_id, Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    db.delete(donor)
    db.commit()
    return 