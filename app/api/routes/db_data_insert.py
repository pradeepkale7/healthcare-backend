from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db



from app.models.file_import import FileImport
from app.models.claim_model import  Claim
from app.models.claim_diagnose_model import ClaimDiagnose
from app.models.patient_model import Patient
from app.models.provider_model import Provider
from app.models.policy_model import Policy
from app.models.processing_log import ProcessingLog



from uuid import uuid4
from datetime import datetime,date
from pydantic import BaseModel
from typing import Optional, List,Any, Tuple
import re

router = APIRouter()

class FrontendDataPayload(BaseModel):
    import_id: str
    filename: str
    mappings: List[dict]
    data: List[dict]
       
        
@router.post("/process")
def process_and_insert_data(
    payload: FrontendDataPayload, 
    db: Session = Depends(get_db)
):
    try:
        # Validate import_id exists
        file_import = db.query(FileImport).filter(FileImport.import_id == payload.import_id).first()
        if not file_import:
            raise HTTPException(status_code=404, detail="File import record not found")

        # Initialize counters
        stats = {
            'total_fields': 0,
            'processed_fields': 0,
            'failed_fields': 0,
            'total_rows': len(payload.data),
            'processed_rows': 0,
            'failed_rows': 0,
            'entity_counts': {
                'patients': 0,
                'providers': 0,
                'policies': 0,
                'claims': 0,
                'diagnoses': 0
            }
        }

        # Process mappings and log them
        for mapping in payload.mappings:
            log = ProcessingLog(
                import_id=payload.import_id,
                header=mapping["header"],
                llm_suggestion=mapping.get("llm_suggestion"),
                final_mapping=mapping["final_mapping"],
                confidence_score=mapping.get("confidence_score"),
                user_edited_mapping=mapping.get('user_edited_mapping', False)
            )
            db.add(log)
        
        file_import.processing_status = "Mapping"
        db.commit()

        # Filter valid mappings
        valid_mappings = [m for m in payload.mappings if m.get("final_mapping")]
        column_mapping = {m['header']: m['final_mapping'] for m in valid_mappings}
        
        failed_records = []

        for row in payload.data:
            stats['total_fields'] += len(row)
            row_success = True
            row_errors = []
            
            # Initialize entities
            patient_data = {}
            provider_data = {}
            policy_data = {}
            claim_data = {}
            diagnoses_data = []
            
            for header, value in row.items():
                
                    target_column = column_mapping.get(header)
                    if not target_column:
                        continue
                    
                    # Clean and convert values
                    cleaned_value, error = clean_field_value(target_column, value)
                    if error:
                        row_errors.append(f"{header}: {error}")
                        stats['failed_fields'] += 1
                        continue
                        
                    stats['processed_fields'] += 1
                    
                    # Route to appropriate entity
                    if target_column in ["member_id", "first_name", "last_name", "dob", "gender", "email", "phone", "address"]:
                        patient_data[target_column] = cleaned_value
                    elif target_column in ["npi_number", "provider_name"]:
                        provider_data[target_column] = cleaned_value
                    elif target_column in ["policy_number", "plan_name", "group_number", "policy_start_date", "policy_end_date"]:
                        policy_data[target_column] = cleaned_value
                    elif target_column in ["diagnosis_code", "diagnosis_description"]:
                        diagnoses_data.append({target_column: cleaned_value})
                    else:
                        claim_data[target_column] = cleaned_value
                        
                
            
            # Process the row if we have any valid data
            try:
                if patient_data or provider_data or policy_data or claim_data or diagnoses_data:
                    # Insert patient
                    patient_id = None
                    if patient_data:
                        patient = Patient(
                            patient_id=uuid4(),
                            **{k: v for k, v in patient_data.items() if k in Patient.__table__.columns}
                        )
                        db.add(patient)
                        db.flush()
                        patient_id = patient.patient_id
                        stats['entity_counts']['patients'] += 1
                    
                    # Insert provider
                    provider_id = None
                    if provider_data:
                        provider = Provider(
                            provider_id=uuid4(),
                            **{k: v for k, v in provider_data.items() if k in Provider.__table__.columns}
                        )
                        db.add(provider)
                        db.flush()
                        provider_id = provider.provider_id
                        stats['entity_counts']['providers'] += 1
                    
                    # Insert policy
                    policy_id = None
                    if policy_data and provider_id:
                        policy = Policy(
                            policy_id=uuid4(),
                            provider_id=provider_id,
                            **{k: v for k, v in policy_data.items() if k in Policy.__table__.columns}
                        )
                        db.add(policy)
                        db.flush()
                        policy_id = policy.policy_id
                        stats['entity_counts']['policies'] += 1
                    
                    # Insert claim
                    claim = Claim(
                        claim_id=uuid4(),
                        import_id=payload.import_id,
                        patient_id=patient_id,
                        provider_id=provider_id,
                        policy_id=policy_id,
                        **{k: v for k, v in claim_data.items() if k in Claim.__table__.columns}
                    )
                    db.add(claim)
                    db.flush()
                    stats['entity_counts']['claims'] += 1
                    
                    # Insert diagnoses
                    for diagnosis in diagnoses_data:
                        claim_diagnose = ClaimDiagnose(
                            claim_diagnose_id=uuid4(),
                            claim_id=claim.claim_id,
                            **{k: v for k, v in diagnosis.items() if k in ClaimDiagnose.__table__.columns}
                        )
                        db.add(claim_diagnose)
                        stats['entity_counts']['diagnoses'] += 1
                    
                    stats['processed_rows'] += 1
                else:
                    stats['failed_rows'] += 1
                    row_errors.append("No valid data fields found in row")
                    
            except Exception as row_error:
                db.rollback()
                stats['failed_rows'] += 1
                row_errors.append(f"Database insertion error: {str(row_error)}")
                print(f"Error processing row: {row_error}")
            
            if row_errors:
                failed_records.append({
                    "import_id": payload.import_id,
                    "row_data": row,
                    "errors": row_errors
                })

        # Update file import status
        finalize_status = (stats['processed_fields'] / stats['total_fields'])*100  
        if finalize_status >= 70:
            file_import.processing_status = "Success"
        else:
            file_import.processing_status = "Failed"
        file_import.records_extracted_from_file = stats['total_fields']
        file_import.records_inserted_count = stats['processed_fields']
        file_import.records_failed_to_insert_count = stats['failed_fields']
        db.commit()
        
        return {
            "message": "Data processing completed",
            "import_id": payload.import_id,
            "statistics": {
                "fields": {
                    "total": stats['total_fields'],
                    "successful": stats['processed_fields'],
                    "failed": stats['failed_fields'],
                    "success_rate": f"{(stats['processed_fields']/stats['total_fields'])*100:.2f}%" if stats['total_fields'] > 0 else "0%"
                },
                "rows": {
                    "total": stats['total_rows'],
                    "successful": stats['processed_rows'],
                    "failed": stats['failed_rows'],
                    "success_rate": f"{(stats['processed_rows']/stats['total_rows'])*100:.2f}%" if stats['total_rows'] > 0 else "0%"
                },
                "entities_created": stats['entity_counts']
            },
            "failed_records_sample": failed_records[:5]  # Return sample of failures
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process data: {str(e)}"
        )

def clean_field_value(target_column: str, value: Any) -> Tuple[Any, Optional[str]]:
    """Clean and convert field values with error reporting"""
    if value is None:
        return None, "Null value"
        
    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() in ["null", "nil", "none", "--", "unknown"]:
            return None, "Empty or invalid value"

    try:
        # Handle date fields
        if any(x in target_column for x in ["date", "dob"]):
            if isinstance(value, (date, datetime)):
                return value, None
            try:
                # Handle multiple date formats
                if "T" in value:  # ISO format
                    return datetime.fromisoformat(value).date(), None
                else:
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%b %d, %Y", "%Y%m%d"]:
                        try:
                            return datetime.strptime(value, fmt).date(), None
                        except ValueError:
                            continue
                    return None, f"Unrecognized date format: {value}"
            except (ValueError, TypeError):
                return None, f"Invalid date value: {value}"
        
        # Handle numeric fields
        if target_column in ["amount_claimed", "amount_approved"]:
            try:
                if isinstance(value, str):
                    # Remove currency symbols and thousands separators
                    value = re.sub(r"[^\d.]", "", value)
                return float(value), None
            except (ValueError, TypeError):
                return None, f"Invalid numeric value: {value}"
        
        # Handle gender fields
        if target_column == "gender":
            gender_map = {
                'm': 'M', 'male': 'M',
                'f': 'F', 'female': 'F',
                'o': 'O', 'other': 'O'
            }
            normalized = gender_map.get(value.lower().strip(), value)
            if normalized not in ['M', 'F', 'O']:
                return None, f"Invalid gender value: {value}"
            return normalized, None
        
        return value, None
        
    except Exception as e:
        return None, f"Processing error: {str(e)}"
    
