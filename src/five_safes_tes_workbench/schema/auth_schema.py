from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, BeforeValidator, model_validator

from ..common.enums.validator_enums import AuthMode, AuthParamEnums
from ..common.exceptions.auth_errors import AuthValidationError

HttpUrlString = Annotated[str, BeforeValidator(lambda v: str(AnyHttpUrl(v)))]


class AuthValidationModel(BaseModel):
    """
    Pydantic Model for validating the authentication
    configuration of the Five Safes TES Workbench setup.

    Attributes:
    - auth_mode: The authentication mode (ACCESS_TOKEN or CREDENTIALS).

    For ACCESS_TOKEN mode:
        - access_token: The access token for TES submission.
        - id_token: Optional OIDC ID token for object-storage STS retrieval.

    For CREDENTIALS mode:
        - client_id: The Keycloak client ID.
        - client_secret: The Keycloak client secret.
        - keycloak_url: The Keycloak URL.
        - username: The Keycloak username.
        - password: The Keycloak password.
        - id_token: Optional OIDC ID token for STS retrieval. When omitted,
          an id_token is fetched from Keycloak at retrieval time.
    """

    model_config = {"frozen": True}

    auth_mode: AuthMode = AuthMode.CREDENTIALS

    access_token: str | None = None
    id_token: str | None = None

    client_id: str | None = None
    client_secret: str | None = None
    keycloak_url: HttpUrlString | None = None
    username: str | None = None
    password: str | None = None

    @model_validator(mode="before")
    @classmethod
    def resolve_auth(cls, values: dict[str, object]) -> dict[str, object]:
        for field in ("access_token", "id_token"):
            token: object = values.get(field)
            if isinstance(token, str):
                values[field] = token.strip()

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

        self._validate_id_token_if_present()
        return self

    def _validate_access_token(self) -> None:
        if not self.access_token:
            raise AuthValidationError(
                ["Access token must not be empty for ACCESS_TOKEN auth mode."]
            )

    def _validate_credentials(self) -> None:
        optional_fields = {AuthParamEnums.ACCESS_TOKEN, AuthParamEnums.ID_TOKEN}
        credential_fields = [
            e.value for e in AuthParamEnums if e not in optional_fields
        ]
        missing = [
            field
            for field in credential_fields
            if getattr(self, field) is None or str(getattr(self, field)).strip() == ""
        ]
        if missing:
            raise AuthValidationError(
                [f"Missing required field: {field}" for field in missing]
            )

    def _validate_id_token_if_present(self) -> None:
        if self.id_token is not None and not self.id_token.strip():
            raise AuthValidationError(["id_token must not be empty when provided."])
