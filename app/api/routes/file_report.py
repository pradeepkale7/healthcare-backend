from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.file_import import FileImport
from app.models.claim_model import  Claim
from app.models.claim_diagnose_model import ClaimDiagnose
from app.models.patient_model import Patient
from app.models.provider_model import Provider
from app.models.policy_model import Policy
from app.models.processing_log import ProcessingLog
from typing import Optional
from sqlalchemy import func, distinct

router = APIRouter()

# Mapping final_mapping column names to SQLAlchemy models
COLUMN_TO_MODEL = {
    "member_id": Patient,
    "first_name": Patient,
    "last_name": Patient,
    "gender": Patient,
    "dob": Patient,
    "email": Patient,
    "phone": Patient,
    "address": Patient,
    "npi_number": Provider,
    "provider_name": Provider,
    "policy_number": Policy,
    "plan_name": Policy,
    "group_number": Policy,
    "policy_start_date": Policy,
    "policy_end_date": Policy,
    "claim_date": Claim,
    "admission_date": Claim,
    "discharge_date": Claim,
    "amount_claimed": Claim,
    "amount_approved": Claim,
    "claim_status": Claim,
    "rejection_reason": Claim,
    "diagnosis_code": ClaimDiagnose,
    "diagnosis_description": ClaimDiagnose
}

@router.get("/report/{import_id}")
def get_file_report(import_id: str, db: Session = Depends(get_db)):
    try:
        file_import = db.query(FileImport).filter(FileImport.import_id == import_id).first()
        if not file_import:
            raise HTTPException(status_code=404, detail="File not found")

        total_records = file_import.records_extracted_from_file
        inserted = file_import.records_inserted_count
        failed = file_import.records_failed_to_insert_count

        stats = {
            "total_records_extracted": total_records,
            "records_inserted": inserted,
            "records_failed": failed,
            "claims_created": db.query(Claim).filter(Claim.import_id == import_id).count(),
            "patients_created": db.query(Patient).join(Claim).filter(Claim.import_id == import_id).distinct().count(),
            "providers_created": db.query(Provider).join(Claim).filter(Claim.import_id == import_id).distinct().count(),
            "policies_created": db.query(Policy).join(Claim).filter(Claim.import_id == import_id).distinct().count(),
            "diagnoses_created": db.query(ClaimDiagnose).join(Claim).filter(Claim.import_id == import_id).count()
        }

        log_entries = db.query(ProcessingLog).filter(ProcessingLog.import_id == import_id).all()
        column_mappings = []
        fully_populated = partially_populated = empty_columns = 0
        llm_mapped = manually_mapped = unmapped = 0
        total_file_headers = len(log_entries)


        for log in log_entries:
            header = log.header
            matched_column = log.final_mapping 
            suggestion = log.llm_suggestion 
            edited = log.user_edited_mapping
            confidence = log.confidence_score
            records_populated = 0
            empty_values = 0
            inserted_values = []
            
            if edited :
                manually_mapped += 1
            if matched_column == "Unmapped":
                unmapped += 1   
            if suggestion == matched_column:
                llm_mapped += 1
            
            if matched_column:
                model = COLUMN_TO_MODEL.get(matched_column)
                if model:
                    col = getattr(model, matched_column, None)
                    if col is not None:
                        # For patient-related fields, count only patients linked to this import's claims
                        query_base = db.query(col)

                        # For patient-related fields
                        if model == Patient:
                            base_query = query_base.join(Claim, Claim.patient_id == Patient.patient_id).filter(Claim.import_id == import_id)
                        elif model == Provider:
                            base_query = query_base.join(Claim, Claim.provider_id == Provider.provider_id).filter(Claim.import_id == import_id)
                        elif model == Policy:
                            base_query = query_base.join(Claim, Claim.policy_id == Policy.policy_id).filter(Claim.import_id == import_id)
                        elif model == ClaimDiagnose:
                            base_query = query_base.join(Claim, Claim.claim_id == ClaimDiagnose.claim_id).filter(Claim.import_id == import_id)
                        elif model == Claim:
                            base_query = query_base.filter(Claim.import_id == import_id)
                        else:
                            base_query = query_base  # fallback (shouldn't be used)

                        # Count non-null
                        records_populated = base_query.filter(col.isnot(None)).count()
                        # Count null
                        empty_values = base_query.filter(col.is_(None)).count()
                        # Sample values
                        inserted_values = base_query.filter(col.isnot(None)).limit(10).all()
                        inserted_values = [row[0] for row in inserted_values]

                if records_populated == total_records:
                    fully_populated += 1
                elif 0 < records_populated < total_records:
                    partially_populated += 1
                else:
                    empty_columns += 1
            
                    
                             
            


            column_mappings.append({
                "header": header,
                "matched_column": matched_column,
                "llm_suggestion": suggestion,
                "final_mapping": matched_column,
                "confidence_score": confidence,
                "user_edited": edited,
                "records_populated": records_populated,
                "empty_values": empty_values,
                "inserted_values": inserted_values
            })

        success_rate = round((inserted / total_records) * 100, 2) if total_records else 0.0

        # --- Sample Data Section ---
        sample_claims = db.query(Claim).filter(Claim.import_id == import_id).all()
        sample_patients = (
            db.query(Patient)
            .join(Claim, Claim.patient_id == Patient.patient_id)
            .filter(Claim.import_id == import_id)
            .all()
        )
        sample_providers = (
            db.query(Provider)
            .join(Claim, Claim.provider_id == Provider.provider_id)
            .filter(Claim.import_id == import_id)
            .all()
        )
        sample_policies = (
            db.query(Policy)
            .join(Claim, Claim.policy_id == Policy.policy_id)
            .filter(Claim.import_id == import_id)
            .all()
        )
        sample_diagnoses = (
            db.query(ClaimDiagnose)
            .join(Claim, Claim.claim_id == ClaimDiagnose.claim_id)
            .filter(Claim.import_id == import_id)
            .all()
        )

        # Serialize SQLAlchemy objects to dictionaries (for JSON response)
        def serialize(obj):
            return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}

        return {
            "file_info": {
                "filename": file_import.filename,
                "file_extension": file_import.file_extension,
                "upload_time": file_import.upload_time.isoformat(),
                "processing_status": file_import.processing_status,
                "storage_type": file_import.storage_type
            },
            "statistics": stats,
            "column_mappings": column_mappings,
            "processing_summary": {
                "total_file_headers": total_file_headers,
                "llm_mapped_columns": llm_mapped,
                "manually_mapped_columns": manually_mapped,
                "unmapped_columns": unmapped,
                "fully_populated_columns": fully_populated,
                "partially_populated_columns": partially_populated,
                "empty_columns": empty_columns
            },
            "success_rate": success_rate,
            "sample_data": {
                "claims": [serialize(c) for c in sample_claims],
                "patients": [serialize(p) for p in sample_patients],
                "providers": [serialize(p) for p in sample_providers],
                "policies": [serialize(p) for p in sample_policies],
                "diagnoses": [serialize(d) for d in sample_diagnoses],
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")







