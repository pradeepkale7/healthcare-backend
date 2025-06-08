from sqlalchemy import Column, String, Integer, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class FileImport(Base):
    __tablename__ = "file_import"

    import_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(Text, nullable=False)
    file_extension = Column(String(10), nullable=False)
    storage_type = Column(String(10), nullable=False)
    local_path = Column(String(512))
    s3_bucket = Column(String(255))
    s3_key = Column(String(512))
    processing_status = Column(String, nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    records_extracted_from_file = Column(Integer, default=0)
    records_inserted_count = Column(Integer, default=0)
    records_failed_to_insert_count = Column(Integer, default=0)

    __table_args__ = (
        CheckConstraint("storage_type IN ('local', 's3')"),
        CheckConstraint(
            "(storage_type = 'local' AND local_path IS NOT NULL) OR "
            "(storage_type = 's3' AND s3_bucket IS NOT NULL AND s3_key IS NOT NULL)",
            name="valid_storage_path"
        )
    )
