from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class OrganizationEmailTemplateBase(BaseModel):
    template_type: str
    content: str
    is_active: Optional[bool] = True

class OrganizationEmailTemplateCreate(OrganizationEmailTemplateBase):
    pass

class OrganizationEmailTemplateUpdate(BaseModel):
    content: Optional[str]
    is_active: Optional[bool]

class OrganizationEmailTemplateResponse(OrganizationEmailTemplateBase):
    id: UUID
    organization_id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True 