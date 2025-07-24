from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class DonationBase(BaseModel):
    donor_id: UUID
    amount: float
    date: datetime
    purpose: str
    payment_mode: str
    payment_details: Optional[Dict[str, Any]] = None
    receipt_path: Optional[str] = None
    receipt_number: Optional[str] = None
    email_sent: Optional[bool] = False
    whatsapp_sent: Optional[bool] = False

class DonationCreate(DonationBase):
    pass

class DonationUpdate(BaseModel):
    amount: Optional[float]
    date: Optional[datetime]
    purpose: Optional[str]
    payment_mode: Optional[str]
    payment_details: Optional[Dict[str, Any]]
    receipt_path: Optional[str]
    receipt_number: Optional[str]
    email_sent: Optional[bool]
    whatsapp_sent: Optional[bool]

class DonationResponse(DonationBase):
    id: UUID
    organization_id: UUID
    created_at: Optional[datetime]

    class Config:
        orm_mode = True 