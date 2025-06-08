# app/models/claim_diagnose_model.py
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from app.core.database import Base

class ClaimDiagnose(Base):
    __tablename__ = "claim_diagnose"

    claim_diagnose_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"))
    diagnosis_code = Column(String)
    diagnosis_description = Column(String)
