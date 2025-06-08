from sqlalchemy import Column, String, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class ProcessingLog(Base):
    __tablename__ = "processing_log"
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(UUID(as_uuid=True), ForeignKey("file_import.import_id", ondelete="CASCADE"), nullable=False)
    log_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    header = Column(String, nullable=False)
    llm_suggestion = Column(String)
    final_mapping = Column(String)
    confidence_score = Column(Float)
    user_edited_mapping = Column(Boolean, default=False)
