import os
from enum import Enum

class StorageType(str, Enum):
    LOCAL = "local"
    S3 = "s3"

STORAGE_TYPE = os.getenv("STORAGE_TYPE", StorageType.LOCAL)  # switch to 's3' in prod
