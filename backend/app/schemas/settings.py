from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class OrganizationSettingsBase(BaseModel):
    setting_key: str
    setting_value: Dict[str, Any]

class OrganizationSettingsCreate(OrganizationSettingsBase):
    pass

class OrganizationSettingsUpdate(BaseModel):
    setting_value: Optional[Dict[str, Any]]

class OrganizationSettingsResponse(OrganizationSettingsBase):
    id: UUID
    organization_id: UUID
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True 