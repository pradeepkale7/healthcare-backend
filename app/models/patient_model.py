# app/models/patient_model.py
from sqlalchemy import Column, String, Date, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patient"

    patient_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    dob = Column(Date)
    gender = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
