"""Tests for WorkbenchValidateBuilder, WorkbenchTESBuilder, and WorkbenchSubmitBuilder."""

import yaml
import pytest
from unittest.mock import MagicMock, patch

from five_safes_tes_workbench.core.validate_builder import WorkbenchValidateBuilder
from five_safes_tes_workbench.core.tes_builder import WorkbenchTESBuilder
from five_safes_tes_workbench.core.submit_builder import WorkbenchSubmitBuilder
from five_safes_tes_workbench.schema.config_schema import ConfigValidationModel
from five_safes_tes_workbench.schema.auth_schema import AuthValidationModel
from five_safes_tes_workbench.common.validator_enums import AuthMode


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

VALID_KWARGS = {
    "project": "my-project",
    "tes_base_url": "https://tes.example.com",
    "minio_sts_endpoint": "https://sts.example.com",
    "minio_endpoint": "minio.example.com:9000",
    "minio_output_bucket": "output-bucket",
    "tres": ["TRE-A"],
    "access_token": "tok-abc123",
}

REQUIRED_TES_PARAMS = {
    "image": "alpine:latest",
    "command": ["echo", "hello"],
}


def _make_config() -> ConfigValidationModel:
    return ConfigValidationModel(
        project="my-project",
        tes_base_url="https://tes.example.com",
        minio_sts_endpoint="https://sts.example.com",
        minio_endpoint="minio.example.com:9000",
        minio_output_bucket="output-bucket",
        tres=["TRE-A"],
    )


def _make_auth_token() -> AuthValidationModel:
    return AuthValidationModel(access_token="tok-abc123")


def _make_auth_credentials() -> AuthValidationModel:
    return AuthValidationModel(
        client_id="my-client",
        client_secret="secret",
        keycloak_url="https://keycloak.example.com",
        username="user",
        password="pass",
    )


# ---------------------------------------------------------------------------
# WorkbenchValidateBuilder
# ---------------------------------------------------------------------------


class TestWorkbenchValidateBuilder:
    def test_config_property_raises_before_validate(self):
        builder = WorkbenchValidateBuilder()
        with pytest.raises(ValueError, match="validate"):
            _ = builder.config

    def test_auth_property_raises_before_validate(self):
        builder = WorkbenchValidateBuilder()
        with pytest.raises(ValueError, match="validate"):
            _ = builder.auth

    def test_validate_with_no_args_raises(self):
        builder = WorkbenchValidateBuilder()
        with pytest.raises(ValueError, match="config_path"):
            builder.validate()

    def test_validate_with_kwargs(self):
        builder = WorkbenchValidateBuilder()
        builder.validate(**VALID_KWARGS)
        assert builder.config.project == "my-project"
        assert builder.auth.auth_mode == AuthMode.ACCESS_TOKEN

    def test_validate_with_credentials_kwargs(self):
        builder = WorkbenchValidateBuilder()
        builder.validate(
            project="my-project",
            tes_base_url="https://tes.example.com",
            minio_sts_endpoint="https://sts.example.com",
            minio_endpoint="minio.example.com:9000",
            minio_output_bucket="output-bucket",
            tres=["TRE-A"],
            client_id="cid",
            client_secret="csec",
            keycloak_url="https://kc.example.com",
            username="u",
            password="p",
        )
        assert builder.auth.auth_mode == AuthMode.CREDENTIALS

    def test_validate_with_yaml_file(self, tmp_path):
        data = {
            "config": {
                "project": "yaml-project",
                "tes_base_url": "https://tes.example.com",
                "minio_sts_endpoint": "https://sts.example.com",
                "minio_endpoint": "minio.example.com",
                "minio_output_bucket": "bucket",
                "tres": ["TRE-X"],
            },
            "auth": {"access_token": "yaml-token"},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(data))

        builder = WorkbenchValidateBuilder()
        builder.validate(config_path=str(config_file))
        assert builder.config.project == "yaml-project"
        assert builder.auth.access_token == "yaml-token"

    def test_validate_with_missing_yaml_file_raises(self):
        builder = WorkbenchValidateBuilder()
        with pytest.raises(FileNotFoundError):
            builder.validate(config_path="/nonexistent/config.yaml")


# ---------------------------------------------------------------------------
# WorkbenchTESBuilder
# ---------------------------------------------------------------------------


class TestWorkbenchTESBuilder:
    def test_tes_task_property_raises_before_build(self):
        builder = WorkbenchTESBuilder()
        with pytest.raises(ValueError, match="build_tes"):
            _ = builder.tes_task

    def test_build_sets_tes_task(self):
        builder = WorkbenchTESBuilder()
        builder.build(_make_config(), REQUIRED_TES_PARAMS)
        assert builder.tes_task is not None

    def test_build_uses_provided_image_and_command(self):
        builder = WorkbenchTESBuilder()
        builder.build(
            _make_config(), {"image": "ubuntu:22.04", "command": ["ls", "-la"]}
        )
        executor = builder.tes_task.executors[0]
        assert executor.image == "ubuntu:22.04"
        assert executor.command == ["ls", "-la"]

    def test_build_uses_default_name_and_description(self):
        builder = WorkbenchTESBuilder()
        builder.build(_make_config(), REQUIRED_TES_PARAMS)
        assert builder.tes_task.name == "Hello World"
        assert builder.tes_task.description == "Hello World"

    def test_build_uses_custom_name_and_description(self):
        builder = WorkbenchTESBuilder()
        builder.build(
            _make_config(),
            {**REQUIRED_TES_PARAMS, "name": "My Task", "description": "Does stuff"},
        )
        assert builder.tes_task.name == "My Task"
        assert builder.tes_task.description == "Does stuff"

    def test_build_tags_include_project_and_tres(self):
        config = _make_config()
        builder = WorkbenchTESBuilder()
        builder.build(config, REQUIRED_TES_PARAMS)
        tags = builder.tes_task.tags
        assert tags["project"] == config.project
        assert tags["tres"] == ",".join(config.tres)

    def test_build_default_output_path(self):
        builder = WorkbenchTESBuilder()
        builder.build(_make_config(), REQUIRED_TES_PARAMS)
        output = builder.tes_task.outputs[0]
        assert output.path == "/outputs"
        assert output.url == "s3://"

    def test_build_custom_output(self):
        builder = WorkbenchTESBuilder()
        builder.build(
            _make_config(),
            {
                **REQUIRED_TES_PARAMS,
                "output_url": "s3://my-bucket",
                "output_path": "/results",
            },
        )
        output = builder.tes_task.outputs[0]
        assert output.url == "s3://my-bucket"
        assert output.path == "/results"

    def test_build_twice_replaces_task(self):
        builder = WorkbenchTESBuilder()
        builder.build(_make_config(), {**REQUIRED_TES_PARAMS, "name": "First"})
        builder.build(_make_config(), {**REQUIRED_TES_PARAMS, "name": "Second"})
        assert builder.tes_task.name == "Second"


# ---------------------------------------------------------------------------
# WorkbenchSubmitBuilder
# ---------------------------------------------------------------------------


class TestWorkbenchSubmitBuilder:
    # --- _resolve_bearer ---

    def test_resolve_bearer_access_token(self):
        auth = _make_auth_token()
        bearer = WorkbenchSubmitBuilder._resolve_bearer(auth)
        assert bearer == "tok-abc123"

    def test_resolve_bearer_credentials_calls_keycloak(self):
        auth = _make_auth_credentials()
        with patch.object(
            WorkbenchSubmitBuilder, "_fetch_keycloak_token", return_value="kc-token"
        ) as mock_kc:
            bearer = WorkbenchSubmitBuilder._resolve_bearer(auth)
            mock_kc.assert_called_once_with(auth)
            assert bearer == "kc-token"

    # --- _fetch_keycloak_token ---

    def test_fetch_keycloak_token_posts_to_correct_url(self):
        auth = _make_auth_credentials()
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "fresh-token"}

        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            return_value=mock_response,
        ) as mock_post:
            token = WorkbenchSubmitBuilder._fetch_keycloak_token(auth)

        expected_url = "https://keycloak.example.com/realms/Dare-Control/protocol/openid-connect/token"
        actual_url = mock_post.call_args[0][0]
        assert actual_url == expected_url
        assert token == "fresh-token"
        mock_response.raise_for_status.assert_called_once()

    # --- submit ---

    def _make_tes_task(self):
        import tes

        return tes.Task(
            name="Test",
            executors=[tes.Executor(image="alpine", command=["echo", "hi"])],
        )

    def test_submit_posts_to_correct_endpoint(self):
        config = _make_config()
        auth = _make_auth_token()
        task = self._make_tes_task()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "task-42"}

        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            return_value=mock_response,
        ):
            submitter = WorkbenchSubmitBuilder()
            task_id = submitter.submit(config=config, auth=auth, task=task)

        assert task_id == "task-42"

    def test_submit_uses_bearer_token_in_header(self):
        config = _make_config()
        auth = _make_auth_token()
        task = self._make_tes_task()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "task-99"}

        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            return_value=mock_response,
        ) as mock_post:
            WorkbenchSubmitBuilder().submit(config=config, auth=auth, task=task)

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer tok-abc123"

    def test_submit_retries_on_401_with_credentials(self):
        config = _make_config()
        auth = _make_auth_credentials()
        task = self._make_tes_task()

        response_401 = MagicMock()
        response_401.status_code = 401

        response_200 = MagicMock()
        response_200.status_code = 200
        response_200.json.return_value = {"id": "retried-task"}

        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            side_effect=[response_401, response_200],
        ) as mock_post:
            with patch.object(
                WorkbenchSubmitBuilder,
                "_fetch_keycloak_token",
                return_value="fresh-kc-token",
            ):
                submitter = WorkbenchSubmitBuilder()
                task_id = submitter.submit(config=config, auth=auth, task=task)

        assert task_id == "retried-task"
        assert mock_post.call_count == 2

    def test_submit_raises_on_non_401_http_error(self):
        config = _make_config()
        auth = _make_auth_token()
        task = self._make_tes_task()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server Error")

        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            return_value=mock_response,
        ):
            with pytest.raises(Exception, match="Server Error"):
                WorkbenchSubmitBuilder().submit(config=config, auth=auth, task=task)
