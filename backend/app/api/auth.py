from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.core.security import hash_password, verify_password, create_access_token, get_current_org
from app.models.organization import Organization
from app.core.config import get_settings
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=TokenResponse)
def register(org: OrganizationCreate, db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.email == org.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization already registered")
    hashed_pwd = hash_password(org.password)
    new_org = Organization(
        name=org.name,
        email=org.email,
        password_hash=hashed_pwd,
        slug=org.slug,
        office_address=org.office_address,
        phone=org.phone,
        website=org.website,
        registration_number=org.registration_number,
        pan_number=org.pan_number,
        csr_number=org.csr_number,
        tax_exemption_number=org.tax_exemption_number,
        social_media=org.social_media,
        signature_holder=org.signature_holder,
        status=org.status,
        email_verified=org.email_verified
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    token = create_access_token({"org_id": str(new_org.id)})
    return TokenResponse(access_token=token)

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.email == data.email).first()
    if not org or not verify_password(data.password, org.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"org_id": str(org.id)})
    return TokenResponse(access_token=token)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password", status_code=204)
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or not verify_password(data.old_password, org.password_hash):
        raise HTTPException(status_code=401, detail="Invalid current password")
    org.password_hash = hash_password(data.new_password)
    db.commit()
    return

@router.get("/me", response_model=OrganizationResponse)
def get_me(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org 