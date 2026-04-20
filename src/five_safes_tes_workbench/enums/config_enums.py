from enum import Enum

class ConfigKey(str, Enum):
    """
    Maps configuration file keys to model field names.

    Enum member name  = identifier
    Enum value        = field name used in the model
    """
    PROJECT = "project"
    TES_BASE_URL = "tes_base_url"
    MINIO_STS_ENDPOINT = "minio_sts_endpoint"
    MINIO_ENDPOINT = "minio_endpoint"
    MINIO_OUTPUT_BUCKET = "minio_output_bucket"
    TRES = "tres"