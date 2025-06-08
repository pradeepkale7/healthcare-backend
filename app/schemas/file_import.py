from datetime import datetime
from typing import Optional,List
from pydantic import BaseModel, Field
from uuid import UUID as PyUUID

class FileImportCreate(BaseModel):
    filename: str
    file_extension: str
    storage_type: str
    local_path: Optional[str]
    s3_bucket: Optional[str]
    s3_key: Optional[str]
    processing_status: str
    
class FileImportRead(FileImportCreate):
    import_id: PyUUID
    upload_time: datetime
    records_extracted_from_file: int
    records_inserted_count: int
    records_failed_to_insert_count: Optional[int]    


