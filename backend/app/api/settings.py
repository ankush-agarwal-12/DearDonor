from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.session import get_db
from app.models.settings import OrganizationSettings
from app.models.organization import Organization
from app.core.security import get_current_org

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=Dict[str, Any])
def get_settings(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    # Get org profile
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org_dict = {
        "name": org.name,
        "office_address": org.office_address,
        "phone": org.phone,
        "email": org.email,
        "website": org.website,
        "registration_number": org.registration_number,
        "pan_number": org.pan_number,
        "csr_number": org.csr_number,
        "tax_exemption_number": org.tax_exemption_number,
        "social_media": org.social_media,
        "signature_holder": org.signature_holder,
        "status": org.status,
        "email_verified": org.email_verified,
        "id": str(org.id),
        "created_at": org.created_at,
        "updated_at": org.updated_at,
        "last_login": org.last_login
    }
    # Get all settings
    settings = db.query(OrganizationSettings).filter(OrganizationSettings.organization_id == org_id).all()
    result = {s.setting_key: s.setting_value for s in settings}
    result["organization"] = org_dict
    return result

@router.put("/", response_model=Dict[str, Any])
def update_settings(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    # Update org profile if present
    if "organization" in data:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        for field, value in data["organization"].items():
            if hasattr(org, field):
                setattr(org, field, value)
        db.commit()
    # Update other settings
    for key, value in data.items():
        if key == "organization":
            continue
        setting = db.query(OrganizationSettings).filter(
            OrganizationSettings.organization_id == org_id,
            OrganizationSettings.setting_key == key
        ).first()
        if setting:
            setting.setting_value = value
        else:
            setting = OrganizationSettings(
                organization_id=org_id,
                setting_key=key,
                setting_value=value
            )
            db.add(setting)
    db.commit()
    # Return updated settings
    return get_settings(db, org_id)

@router.get("/{key}", response_model=Any)
def get_setting_key(key: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    setting = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == org_id,
        OrganizationSettings.setting_key == key
    ).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting.setting_value

@router.put("/{key}", response_model=Any)
def update_setting_key(key: str, value: Any, db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    setting = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == org_id,
        OrganizationSettings.setting_key == key
    ).first()
    if setting:
        setting.setting_value = value
    else:
        setting = OrganizationSettings(
            organization_id=org_id,
            setting_key=key,
            setting_value=value
        )
        db.add(setting)
    db.commit()
    return value 