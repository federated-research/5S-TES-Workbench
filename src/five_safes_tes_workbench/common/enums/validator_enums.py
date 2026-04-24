from enum import Enum


class ConfigParamEnums(str, Enum):
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


class AuthMode(str, Enum):
    """
    Defines authentication modes for the Workbench.
    """

    ACCESS_TOKEN = "token"  # nosec B105
    CREDENTIALS = "credentials"


class AuthParamEnums(str, Enum):
    """
    Maps auth configuration keys to model field names.
    """

    ACCESS_TOKEN = "access_token"   # nosec B105
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"  # nosec B105
    KEYCLOAK_URL = "keycloak_url"
    USERNAME = "username"
    PASSWORD = "password"  # nosec B105
