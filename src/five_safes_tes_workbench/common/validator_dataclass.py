from pydantic import BaseModel
from .validator_enums import AuthMode


class ConfigValidationDataModel(BaseModel):
    """
    Data class representing the configuration for 
    validating the Five Safes TES Workbench setup. 

    Attributes:
    ----------
        project (str): The name of the project to validate.
        tes_base_url (str): The base URL of the TES service.
        minio_sts_endpoint (str): The endpoint for MinIO STS (Security Token Service).
        minio_endpoint (str): The endpoint for MinIO.
        minio_output_bucket (str): The name of the MinIO bucket for output.
        tres (Tuple[str, ...]): A tuple of TES endpoints to validate against.
    """
    model_config = {'frozen': True}

    project: str
    tes_base_url: str
    minio_sts_endpoint: str
    minio_endpoint: str
    minio_output_bucket: str
    tres: tuple[str, ...]


class AuthValidationDataModel(BaseModel):
    """
    Data class representing the authentication configuration for
    validating the Five Safes TES Workbench setup.
    
    Attributes:
    - auth_mode (AuthMode): The authentication mode (ACCESS_TOKEN or CREDENTIALS).

    For ACCESS_TOKEN mode:
        - access_token (str): The access token for authentication.

    For CREDENTIALS mode:
        - client_id (str): The Keycloak client ID for submission.
        - client_secret (str): The Keycloak client secret for submission.
        - keycloak_url (str): The Keycloak URL for submission.
        - username (str): The Keycloak username for submission.
        - password (str): The Keycloak password for submission.
    """
    model_config = {'frozen': True}

    auth_mode: AuthMode

    # Token
    access_token: str | None = None

    # Credentials
    client_id: str | None = None
    client_secret: str | None = None
    keycloak_url: str | None = None
    username: str | None = None
    password: str | None = None