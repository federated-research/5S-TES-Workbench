from typing import Annotated
from pydantic import AnyHttpUrl, BeforeValidator

from pydantic import BaseModel, model_validator
from ..common.validator_dataclass import AuthValidationDataModel, AuthMode

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
    auth_mode: AuthMode | None = None

    access_token: str | None = None

    client_id: str | None = None
    client_secret: str | None = None
    keycloak_url: HttpUrlString | None = None
    username: str | None = None
    password: str | None = None

    @model_validator(mode="after")
    def validate_auth(self) -> "AuthValidationModel":
        auth_mode = self._check_auth_mode()

        if auth_mode == AuthMode.ACCESS_TOKEN:
            self._validate_access_token()
        else:
            self._validate_credentials()

        return self
    

    def _check_auth_mode(self) -> AuthMode:
        if self.access_token is not None:
            return AuthMode.ACCESS_TOKEN
        return AuthMode.CREDENTIALS
    

    def _validate_access_token(self) -> None:
        if self.access_token is None or self.access_token.strip() == "":
            raise ValueError(
                "Access token must not be empty for ACCESS_TOKEN auth mode."
            )
        self.access_token = self.access_token.strip()
        

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
        

    def to_validated_config(self) -> AuthValidationDataModel:
        """
        Validates the configuration based on the auth mode
        and returns an immutable dataclass representation of the
        authentication configuration.
        """
        auth_mode = self._check_auth_mode()

        if auth_mode == AuthMode.ACCESS_TOKEN:
            return AuthValidationDataModel(
                auth_mode=auth_mode,
                access_token=self.access_token,
            )

        return AuthValidationDataModel(
            auth_mode=auth_mode,
            client_id=self.client_id,
            client_secret=self.client_secret,
            keycloak_url=self.keycloak_url,
            username=self.username,
            password=self.password,
        )