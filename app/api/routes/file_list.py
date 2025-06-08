from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.file_import import FileImport

router = APIRouter()

@router.get("/files")
def list_uploaded_files(db: Session = Depends(get_db)):
    files = (
        db.query(FileImport)
        .order_by(FileImport.upload_time.desc())
        .all()
    )

    return [
        {
            "import_id": file.import_id,
            "filename": file.filename,
            "file_extension": file.file_extension,
            "upload_time": file.upload_time.isoformat(),
            "processing_status": file.processing_status,
            "records_extracted": file.records_extracted_from_file,
            "records_inserted": file.records_inserted_count,
            "records_failed": file.records_failed_to_insert_count,
            "storage_type": file.storage_type
        }
        for file in files
    ]


