from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid
import datetime

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True)
    office_address = Column(Text)
    phone = Column(Text)
    website = Column(Text)
    registration_number = Column(Text)
    pan_number = Column(Text)
    csr_number = Column(Text)
    tax_exemption_number = Column(Text)
    social_media = Column(JSON, default={})
    signature_holder = Column(JSON, default={})
    status = Column(Text, default="active")
    email_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('email', name='uq_organizations_email'),
        UniqueConstraint('slug', name='uq_organizations_slug'),
    ) 