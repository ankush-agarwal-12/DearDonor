from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
from app.db.session import get_db
from app.models.settings import OrganizationSettings
from app.models.organization import Organization
from app.core.security import get_current_org

router = APIRouter(prefix="/settings", tags=["Settings"])

# Keys that should be parsed as JSON
JSON_KEYS = {"receipt_format", "donation_purposes", "payment_methods", "social_media", "signature_holder", "email_config"}

def parse_setting_value(key: str, value: Any) -> Any:
    """Parse setting value based on key type"""
    if key in JSON_KEYS:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value
    return value

def serialize_setting_value(key: str, value: Any) -> Any:
    """Serialize setting value for storage"""
    if key in JSON_KEYS and not isinstance(value, str):
        return value  # FastAPI will handle JSON serialization
    return value

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
        "tax_exemption_number": org.tax_exemption_number,  # Keep for backward compatibility
        "tax_exemption_12a": org.tax_exemption_12a,        # New 12A field
        "tax_exemption_80g": org.tax_exemption_80g,        # New 80G field
        "social_media": org.social_media,
        "signature_holder": org.signature_holder,
        "status": org.status,
        "email_verified": org.email_verified,
        "id": str(org.id),
        "created_at": org.created_at,
        "updated_at": org.updated_at,
        "last_login": org.last_login
    }
    # Get all settings and parse them appropriately
    settings = db.query(OrganizationSettings).filter(OrganizationSettings.organization_id == org_id).all()
    result = {}
    for s in settings:
        result[s.setting_key] = parse_setting_value(s.setting_key, s.setting_value)
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
        serialized_value = serialize_setting_value(key, value)
        setting = db.query(OrganizationSettings).filter(
            OrganizationSettings.organization_id == org_id,
            OrganizationSettings.setting_key == key
        ).first()
        if setting:
            setting.setting_value = serialized_value
        else:
            setting = OrganizationSettings(
                organization_id=org_id,
                setting_key=key,
                setting_value=serialized_value
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
        # Return default values for known settings
        if key == "receipt_format":
            return {
                "format": "{prefix}/{YY}/{MM}/{XXX}",
                "prefix": "REC",
                "next_sequence": 1
            }
        elif key == "donation_purposes":
            return ["General Fund", "Corpus Fund", "Emergency Fund"]
        elif key == "payment_methods":
            return ["Cash", "UPI", "Bank Transfer", "Cheque"]
        elif key == "email_config":
            return {
                "email_address": "",
                "email_password": "",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True
            }
        else:
            raise HTTPException(status_code=404, detail="Setting not found")
    
    return parse_setting_value(key, setting.setting_value)

@router.put("/{key}", response_model=Any)
def update_setting_key(key: str, value: Any = Body(...), db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    serialized_value = serialize_setting_value(key, value)
    setting = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == org_id,
        OrganizationSettings.setting_key == key
    ).first()
    if setting:
        setting.setting_value = serialized_value
    else:
        setting = OrganizationSettings(
            organization_id=org_id,
            setting_key=key,
            setting_value=serialized_value
        )
        db.add(setting)
    db.commit()
    return parse_setting_value(key, serialized_value) 