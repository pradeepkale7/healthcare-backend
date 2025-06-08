import os
from uuid import uuid4
from app.core.config import STORAGE_TYPE, StorageType



def save_file_locally(file, filename: str):
    upload_dir = "app/uploaded_files"  # ensure this directory exists
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{uuid4()}_{filename}")
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path

def save_file_to_s3(file, filename: str):
    import boto3  # ensure boto3 is installed
    s3 = boto3.client("s3")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    key = f"{uuid4()}_{filename}"
    s3.upload_fileobj(file.file, bucket_name, key)
    return bucket_name, key

def save_file(file, filename: str):
    if STORAGE_TYPE == StorageType.S3:
        return "s3", save_file_to_s3(file, filename)
    else:
        return "local", save_file_locally(file, filename)

