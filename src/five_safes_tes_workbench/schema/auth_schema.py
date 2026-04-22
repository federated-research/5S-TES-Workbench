from typing import Annotated
from pydantic import AnyHttpUrl, BeforeValidator, BaseModel, model_validator
from ..common.validator_enums import AuthMode

HttpUrlString = Annotated[str, BeforeValidator(lambda v: str(AnyHttpUrl(v)))]

class AuthValidationModel(BaseModel):
    """
    Pydantic Model for validating the authentication
    configuration of the Five Safes TES Workbench setup.
    
    Attributes:
    - auth_mode: The authentication mode (ACCESS_TOKEN or CREDENTIALS).
    
    For ACCESS_TOKEN mode:
        - access_token: The access token for authentication.
        
    For CREDENTIALS mode:
        - client_id: The Keycloak client
          ID for submission.
        - client_secret: The Keycloak client
          secret for submission.
        - keycloak_url: The Keycloak URL 
          for submission.
        - username: The Keycloak username 
          for submission.
        - password: The Keycloak password 
          for submission.
    """
    model_config = {"frozen": True}

    auth_mode: AuthMode = AuthMode.CREDENTIALS

    access_token: str | None = None

    client_id: str | None = None
    client_secret: str | None = None
    keycloak_url: HttpUrlString | None = None
    username: str | None = None
    password: str | None = None

    @model_validator(mode="before")
    @classmethod
    def resolve_auth(cls, values: dict[str, object]) -> dict[str, object]:
        token: object = values.get("access_token")
        if isinstance(token, str):
            values["access_token"] = token.strip()

        if values.get("access_token"):
            values["auth_mode"] = AuthMode.ACCESS_TOKEN
        else:
            values["auth_mode"] = AuthMode.CREDENTIALS

        return values
    

    @model_validator(mode="after")
    def validate_auth(self) -> "AuthValidationModel":
        if self.auth_mode == AuthMode.ACCESS_TOKEN:
            self._validate_access_token()
        else:
            self._validate_credentials()

        return self

    def _validate_access_token(self) -> None:
        if not self.access_token:
            raise ValueError(
                "Access token must not be empty for ACCESS_TOKEN auth mode."
            )
        

    def _validate_credentials(self) -> None:
        credential_fields = [
            "client_id",
            "client_secret",
            "keycloak_url",
            "username",
            "password",
        ]
        missing = [
            field for field in credential_fields
            if getattr(self, field) is None 
            or str(getattr(self, field)).strip() == ""
        ]
        if missing:
            raise ValueError(
                f"Missing required fields for CREDENTIALS auth mode: "
                f"{', '.join(missing)}"
            )