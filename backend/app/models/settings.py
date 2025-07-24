from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid
import datetime

class OrganizationSettings(Base):
    __tablename__ = "organization_settings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    setting_key = Column(Text, nullable=False)
    setting_value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow) 