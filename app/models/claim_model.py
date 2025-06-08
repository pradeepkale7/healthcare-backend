# app/models/claim_model.py
from sqlalchemy import Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from app.core.database import Base

class Claim(Base):
    __tablename__ = "claim"

    claim_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_date = Column(Date)
    admission_date = Column(Date)
    discharge_date = Column(Date)
    amount_claimed = Column(Numeric)
    amount_approved = Column(Numeric)
    claim_status = Column(String)
    rejection_reason = Column(String)
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.patient_id"))
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider.provider_id"))
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policy.policy_id"))
    import_id = Column(UUID(as_uuid=True), ForeignKey("file_import.import_id"))
