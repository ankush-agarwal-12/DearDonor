from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.models.organization import Organization
from app.core.security import get_current_org

router = APIRouter(prefix="/organization", tags=["Organization"])

@router.get("/me", response_model=OrganizationResponse)
def get_me(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.put("/me", response_model=OrganizationResponse)
def update_me(
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(org, field, value)
    db.commit()
    db.refresh(org)
    return org 