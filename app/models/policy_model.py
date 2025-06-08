# app/models/policy_model.py
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from app.core.database import Base

class Policy(Base):
    __tablename__ = "policy"

    policy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_number = Column(String)
    plan_name = Column(String)
    group_number = Column(String)
    policy_start_date = Column(Date)
    policy_end_date = Column(Date)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider.provider_id"))
