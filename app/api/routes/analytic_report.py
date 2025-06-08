from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.file_import import FileImport
from app.models.processing_log import ProcessingLog
from sqlalchemy import func

router = APIRouter()

@router.get("/analytics")
def get_full_analytics(db: Session = Depends(get_db)):
    # Get all file imports
    all_files = db.query(
        FileImport.import_id,
        FileImport.filename,
        FileImport.processing_status,
        FileImport.upload_time
    ).order_by(FileImport.upload_time).all()

    # Aggregate stats
    total_uploaded = len(all_files)
    successful_files = sum(1 for f in all_files if f.processing_status == "Success")
    failed_files = sum(1 for f in all_files if f.processing_status == "Failed")
    success_percentage = round((successful_files / total_uploaded) * 100, 2) if total_uploaded else 0

    # Totals from processing logs
    total_inserted = db.query(func.coalesce(func.sum(FileImport.records_inserted_count), 0)).scalar()
    total_failed = db.query(func.coalesce(func.sum(FileImport.records_failed_to_insert_count), 0)).scalar()

    return {
        "summary": {
            "total_uploaded_files": total_uploaded,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "success_percentage": success_percentage,
            "total_records_inserted": total_inserted,
            "total_records_failed": total_failed
        },
        "files": [
            {
                "import_id": f.import_id,
                "filename": f.filename,
                "status": f.processing_status,
                "uploaded_time": f.upload_time.isoformat()
            }
            for f in all_files
        ]
    }
