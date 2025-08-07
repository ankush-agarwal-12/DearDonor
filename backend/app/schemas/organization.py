from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str
    email: EmailStr
    slug: str
    office_address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    pan_number: Optional[str] = None
    csr_number: Optional[str] = None
    tax_exemption_number: Optional[str] = None  # Keep for backward compatibility
    tax_exemption_12a: Optional[str] = None     # New 12A field
    tax_exemption_80g: Optional[str] = None     # New 80G field
    social_media: Optional[Dict[str, Any]] = None
    signature_holder: Optional[Dict[str, Any]] = None
    status: Optional[str] = "active"
    email_verified: Optional[bool] = True

class OrganizationCreate(OrganizationBase):
    password: str

class OrganizationUpdate(BaseModel):
    name: Optional[str]
    office_address: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    registration_number: Optional[str]
    pan_number: Optional[str]
    csr_number: Optional[str]
    tax_exemption_number: Optional[str]  # Keep for backward compatibility
    tax_exemption_12a: Optional[str]     # New 12A field
    tax_exemption_80g: Optional[str]     # New 80G field
    social_media: Optional[Dict[str, Any]]
    signature_holder: Optional[Dict[str, Any]]
    status: Optional[str]

class OrganizationResponse(OrganizationBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_login: Optional[datetime]

    class Config:
        orm_mode = True 