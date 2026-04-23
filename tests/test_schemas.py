"""Tests for Pydantic validation schemas."""

import pytest
from pydantic import ValidationError

from five_safes_tes_workbench.schema.config_schema import ConfigValidationModel
from five_safes_tes_workbench.schema.auth_schema import AuthValidationModel
from five_safes_tes_workbench.schema.validation_schema import WorkbenchValidationModel
from five_safes_tes_workbench.common.validator_enums import AuthMode
from five_safes_tes_workbench.common.validate_params import split_config_params


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_CONFIG = {
    "project": "my-project",
    "tes_base_url": "https://tes.example.com",
    "minio_sts_endpoint": "https://sts.example.com",
    "minio_endpoint": "minio.example.com:9000",
    "minio_output_bucket": "output-bucket",
    "tres": ["TRE-A", "TRE-B"],
}

VALID_AUTH_TOKEN = {"access_token": "tok-abc123"}

VALID_AUTH_CREDENTIALS = {
    "client_id": "my-client",
    "client_secret": "secret",
    "keycloak_url": "https://keycloak.example.com",
    "username": "user",
    "password": "pass",
}


# ---------------------------------------------------------------------------
# ConfigValidationModel
# ---------------------------------------------------------------------------


class TestConfigValidationModel:
    def test_valid_config(self):
        m = ConfigValidationModel(**VALID_CONFIG)
        assert m.project == "my-project"
        assert m.tres == ["TRE-A", "TRE-B"]

    def test_whitespace_is_stripped(self):
        data = {**VALID_CONFIG, "project": "  padded  "}
        m = ConfigValidationModel(**data)
        assert m.project == "padded"

    def test_empty_project_raises(self):
        with pytest.raises(ValidationError, match="project"):
            ConfigValidationModel(**{**VALID_CONFIG, "project": ""})

    def test_whitespace_only_project_raises(self):
        with pytest.raises(ValidationError, match="project"):
            ConfigValidationModel(**{**VALID_CONFIG, "project": "   "})

    def test_invalid_tes_base_url_raises(self):
        with pytest.raises(ValidationError):
            ConfigValidationModel(**{**VALID_CONFIG, "tes_base_url": "not-a-url"})

    def test_invalid_minio_sts_endpoint_raises(self):
        with pytest.raises(ValidationError):
            ConfigValidationModel(**{**VALID_CONFIG, "minio_sts_endpoint": "not-a-url"})

    def test_empty_tres_list_raises(self):
        with pytest.raises(ValidationError, match="tres"):
            ConfigValidationModel(**{**VALID_CONFIG, "tres": []})

    def test_tres_with_blank_entry_raises(self):
        with pytest.raises(ValidationError, match="tres"):
            ConfigValidationModel(**{**VALID_CONFIG, "tres": ["TRE-A", ""]})

    def test_tres_whitespace_entries_stripped_and_validated(self):
        with pytest.raises(ValidationError):
            ConfigValidationModel(**{**VALID_CONFIG, "tres": ["  "]})

    def test_frozen_model_is_immutable(self):
        m = ConfigValidationModel(**VALID_CONFIG)
        with pytest.raises(ValidationError):
            m.project = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AuthValidationModel
# ---------------------------------------------------------------------------


class TestAuthValidationModel:
    def test_access_token_sets_mode(self):
        m = AuthValidationModel(**VALID_AUTH_TOKEN)
        assert m.auth_mode == AuthMode.ACCESS_TOKEN
        assert m.access_token == "tok-abc123"

    def test_access_token_whitespace_is_stripped(self):
        m = AuthValidationModel(access_token="  tok  ")
        assert m.access_token == "tok"

    def test_credentials_mode_sets_mode(self):
        m = AuthValidationModel(**VALID_AUTH_CREDENTIALS)
        assert m.auth_mode == AuthMode.CREDENTIALS

    def test_credentials_mode_missing_field_raises(self):
        incomplete = {
            k: v for k, v in VALID_AUTH_CREDENTIALS.items() if k != "password"
        }
        with pytest.raises(ValidationError, match="password"):
            AuthValidationModel(**incomplete)

    def test_no_auth_raises(self):
        with pytest.raises(ValidationError):
            AuthValidationModel()

    def test_empty_access_token_falls_back_to_credentials_mode_and_raises(self):
        with pytest.raises(ValidationError):
            AuthValidationModel(access_token="")


# ---------------------------------------------------------------------------
# WorkbenchValidationModel
# ---------------------------------------------------------------------------


class TestWorkbenchValidationModel:
    def test_model_validate_combines_config_and_auth(self):
        m = WorkbenchValidationModel.model_validate(
            {
                "config": VALID_CONFIG,
                "auth": VALID_AUTH_TOKEN,
            }
        )
        assert m.config.project == "my-project"
        assert m.auth.auth_mode == AuthMode.ACCESS_TOKEN

    def test_from_yaml_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            WorkbenchValidationModel.from_yaml("/nonexistent/path/config.yaml")


# ---------------------------------------------------------------------------
# split_config_params
# ---------------------------------------------------------------------------


class TestSplitConfigParams:
    def test_splits_correctly(self):
        params = {
            **VALID_CONFIG,
            **VALID_AUTH_TOKEN,
        }
        config, auth = split_config_params(params)  # type: ignore[arg-type]
        assert set(config.keys()) == {
            "project",
            "tes_base_url",
            "minio_sts_endpoint",
            "minio_endpoint",
            "minio_output_bucket",
            "tres",
        }
        assert set(auth.keys()) == {"access_token"}

    def test_unknown_keys_dropped(self):
        params = {**VALID_CONFIG, "access_token": "tok", "unknown_key": "value"}
        config, auth = split_config_params(params)  # type: ignore[arg-type]
        assert "unknown_key" not in config
        assert "unknown_key" not in auth

    def test_empty_params_returns_empty_dicts(self):
        config, auth = split_config_params({})  # type: ignore[arg-type]
        assert config == {}
        assert auth == {}
