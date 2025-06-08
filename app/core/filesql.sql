-- Enable UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. File Import Tracking
CREATE TABLE file_import(
    import_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    storage_type VARCHAR(10) NOT NULL CHECK (storage_type IN ('local', 's3')),
    local_path VARCHAR(512),
    s3_bucket VARCHAR(255),
    s3_key VARCHAR(512),
    processing_status TEXT CHECK (processing_status IN ('Success', 'Failed','Uploaded','Mapping')) NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    records_extracted_from_file INT NOT NULL DEFAULT 0,
    records_inserted_count INT NOT NULL DEFAULT 0,
    records_failed_to_insert_count INT DEFAULT 0,
    CONSTRAINT valid_storage_path CHECK (
        (storage_type = 'local' AND local_path IS NOT NULL) OR
        (storage_type = 's3' AND s3_bucket IS NOT NULL AND s3_key IS NOT NULL)
    )
);

-- 2. Patients
CREATE TABLE patient (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    gender VARCHAR(10),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT
);

-- 3. Providers
CREATE TABLE provider (
    provider_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    npi_number VARCHAR(10) ,
    provider_name VARCHAR(100)
);


-- 5. Policies
CREATE TABLE policy (
    policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_number TEXT,
    provider_id UUID REFERENCES provider(provider_id) ON DELETE SET NULL,
    plan_name VARCHAR(255),
    group_number VARCHAR(100),
    policy_start_date DATE,
    policy_end_date DATE
);

-- 6. Claims
CREATE TABLE claim (
    claim_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    import_id UUID NOT NULL REFERENCES file_import(import_id) ON DELETE CASCADE,

    patient_id UUID REFERENCES patient(patient_id) ON DELETE SET NULL,
    provider_id UUID REFERENCES provider(provider_id) ON DELETE SET NULL,
    policy_id UUID REFERENCES policy(policy_id) ON DELETE SET NULL,

    claim_date DATE,
    admission_date DATE,
    discharge_date DATE,
    amount_claimed NUMERIC(12, 2),
    amount_approved NUMERIC(12, 2),
    claim_status TEXT ,
    rejection_reason TEXT,

    insertion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);



-- 7.1 Claim Diagnoses (Many-to-Many)
CREATE TABLE claim_diagnose (
    claim_diagnose_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claim(claim_id) ON DELETE CASCADE,
    diagnosis_code VARCHAR(50) ,
    diagnosis_description TEXT
);

-- 8. Processing Logs
CREATE TABLE processing_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    import_id UUID NOT NULL REFERENCES file_import(import_id) ON DELETE CASCADE,
    log_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    header TEXT NOT NULL,
    llm_suggestion TEXT,
    final_mapping TEXT,
    confidence_score REAL,
    user_edited_mapping BOOLEAN DEFAULT FALSE
);
