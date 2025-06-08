# app/models/provider_model.py
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from app.core.database import Base

class Provider(Base):
    __tablename__ = "provider"

    provider_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    npi_number = Column(String)
    provider_name = Column(String)
