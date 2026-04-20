from dataclasses import dataclass
from ..enums.auth_enums import AuthMode


@dataclass(frozen=True)
class AuthValidationDataClass:

    auth_mode: AuthMode

    # Token
    access_token: str | None = None

    # Credentials
    submission_keycloak_client_id: str | None = None
    submission_keycloak_client_secret: str | None = None
    submission_keycloak_url: str | None = None
    submission_keycloak_username: str | None = None
    submission_keycloak_password: str | None = None