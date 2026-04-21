from dataclasses import dataclass
from .validator_enums import AuthMode


@dataclass(frozen=True)
class ConfigValidationDataClass:
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

    project: str
    tes_base_url: str
    minio_sts_endpoint: str
    minio_endpoint: str
    minio_output_bucket: str
    tres: tuple[str, ...]


@dataclass(frozen=True)
class AuthValidationDataClass:
    """
    Data class representing the authentication configuration for
    validating the Five Safes TES Workbench setup.
    
    Attributes:
    - auth_mode (AuthMode): The authentication mode (ACCESS_TOKEN or CREDENTIALS).

    For ACCESS_TOKEN mode:
        - access_token (str): The access token for authentication.

    For CREDENTIALS mode:
        - submission_keycloak_client_id (str): The Keycloak client ID for submission.
        - submission_keycloak_client_secret (str): The Keycloak client secret for submission.
        - submission_keycloak_url (str): The Keycloak URL for submission.
        - submission_keycloak_username (str): The Keycloak username for submission.
        - submission_keycloak_password (str): The Keycloak password for submission.
    """

    auth_mode: AuthMode

    # Token
    access_token: str | None = None

    # Credentials
    submission_keycloak_client_id: str | None = None
    submission_keycloak_client_secret: str | None = None
    submission_keycloak_url: str | None = None
    submission_keycloak_username: str | None = None
    submission_keycloak_password: str | None = None