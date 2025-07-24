from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class DonorBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    pan: Optional[str] = None
    donor_type: Optional[str] = "Individual"

class DonorCreate(DonorBase):
    pass

class DonorUpdate(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    address: Optional[str]
    pan: Optional[str]
    donor_type: Optional[str]

class DonorResponse(DonorBase):
    id: UUID
    organization_id: UUID
    created_at: Optional[datetime]

    class Config:
        orm_mode = True 