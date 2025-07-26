from sqlalchemy import Column, String, Text, DateTime, Boolean, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid
import datetime

class Donation(Base):
    __tablename__ = "donations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("donors.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    date = Column(DateTime, nullable=False)
    purpose = Column(Text, nullable=False)
    payment_mode = Column(Text, nullable=False)
    payment_details = Column(JSON, default={})
    receipt_path = Column(Text)
    receipt_number = Column(Text)  # New field for receipt number
    email_sent = Column(Boolean, default=False)
    whatsapp_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow) 