import pytest

from five_safes_tes_workbench.common.exceptions.auth_errors import AuthValidationError
from five_safes_tes_workbench.schema.auth_schema import AuthValidationModel

_CREDENTIALS = {
    "client_id": "Dare-Control-S3",
    "client_secret": "secret",
    "keycloak_url": "https://keycloak.example.com",
    "username": "user",
    "password": "pass",
}


class TestAuthValidationModel:
    def test_credentials_without_id_token_is_valid(self):
        auth = AuthValidationModel.model_validate(_CREDENTIALS)
        assert auth.id_token is None

    def test_credentials_with_id_token_is_valid(self):
        auth = AuthValidationModel.model_validate(
            {**_CREDENTIALS, "id_token": "id-tok-xyz"}
        )
        assert auth.id_token == "id-tok-xyz"

    def test_access_token_mode_without_id_token_is_valid(self):
        auth = AuthValidationModel.model_validate({"access_token": "access-only"})
        assert auth.access_token == "access-only"
        assert auth.id_token is None

    def test_access_token_mode_accepts_both_tokens(self):
        auth = AuthValidationModel.model_validate(
            {"access_token": "access-tok", "id_token": "id-tok"}
        )
        assert auth.access_token == "access-tok"
        assert auth.id_token == "id-tok"

    def test_empty_id_token_is_rejected(self):
        with pytest.raises(AuthValidationError):
            AuthValidationModel.model_validate({**_CREDENTIALS, "id_token": "   "})
