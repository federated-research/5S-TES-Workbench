from pydantic import BaseModel, model_validator
from ..enums.auth_enums import AuthMode
from ..models.auth_dataclass import AuthValidationDataClass


class AuthConfig(BaseModel):

    access_token: str | None = None

    submission_keycloak_client_id: str | None = None
    submission_keycloak_client_secret: str | None = None
    submission_keycloak_url: str | None = None
    submission_keycloak_username: str | None = None
    submission_keycloak_password: str | None = None

    @model_validator(mode="after")
    def validate_auth(self) -> "AuthConfig":
        auth_mode = self._check_auth_mode()

        if auth_mode == AuthMode.ACCESS_TOKEN:
            self._validate_access_token()
        else:
            self._validate_credentials()

        return self
    

    def _check_auth_mode(self) -> AuthMode:
        if self.access_token is not None and self.access_token.strip() != "":
            return AuthMode.ACCESS_TOKEN
        return AuthMode.CREDENTIALS
    

    def _validate_access_token(self) -> None:
        if self.access_token is None or self.access_token.strip() == "":
            raise ValueError(
                "Access token must not be empty for ACCESS_TOKEN auth mode."
            )
        

    def _validate_credentials(self) -> None:
        credential_fields = [
            "submission_keycloak_client_id",
            "submission_keycloak_client_secret",
            "submission_keycloak_url",
            "submission_keycloak_username",
            "submission_keycloak_password",
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
        

    def to_validated_config(self) -> AuthValidationDataClass:
        auth_mode = self._check_auth_mode()

        if auth_mode == AuthMode.ACCESS_TOKEN:
            return AuthValidationDataClass(
                auth_mode=auth_mode,
                access_token=self.access_token,
            )

        return AuthValidationDataClass(
            auth_mode=auth_mode,
            submission_keycloak_client_id=self.submission_keycloak_client_id,
            submission_keycloak_client_secret=self.submission_keycloak_client_secret,
            submission_keycloak_url=self.submission_keycloak_url,
            submission_keycloak_username=self.submission_keycloak_username,
            submission_keycloak_password=self.submission_keycloak_password,
        )