"""Integration tests for the Workbench facade."""

import pytest
from unittest.mock import MagicMock, patch

from five_safes_tes_workbench.workbench import Workbench
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

VALID_TES_PARAMS = {
    "image": "alpine:latest",
    "command": ["echo", "hello"],
}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestWorkbenchInit:
    def test_instantiates_without_error(self):
        wb = Workbench()
        assert wb is not None

    def test_has_validator_task_builder_and_submitter(self):
        wb = Workbench()
        assert hasattr(wb, "_validator")
        assert hasattr(wb, "_task_builder")
        assert hasattr(wb, "_submitter")


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

class TestWorkbenchValidate:
    def test_validate_returns_self_for_chaining(self):
        wb = Workbench()
        result = wb.validate(**VALID_KWARGS)
        assert result is wb

    def test_validate_populates_config(self):
        wb = Workbench()
        wb.validate(**VALID_KWARGS)
        assert wb._validator.config.project == "my-project"

    def test_validate_populates_auth(self):
        wb = Workbench()
        wb.validate(**VALID_KWARGS)
        assert wb._validator.auth.auth_mode == AuthMode.ACCESS_TOKEN

    def test_validate_with_no_args_raises(self):
        wb = Workbench()
        with pytest.raises(ValueError):
            wb.validate()


# ---------------------------------------------------------------------------
# build_tes()
# ---------------------------------------------------------------------------

class TestWorkbenchBuildTes:
    def test_build_tes_returns_self_for_chaining(self):
        wb = Workbench()
        wb.validate(**VALID_KWARGS)
        result = wb.build_tes(**VALID_TES_PARAMS)
        assert result is wb

    def test_build_tes_without_validate_raises(self):
        wb = Workbench()
        with pytest.raises(ValueError, match="validate"):
            wb.build_tes(**VALID_TES_PARAMS)

    def test_build_tes_sets_task(self):
        wb = Workbench()
        wb.validate(**VALID_KWARGS).build_tes(**VALID_TES_PARAMS)
        task = wb._task_builder.tes_task
        assert task.executors[0].image == "alpine:latest"


# ---------------------------------------------------------------------------
# submit()
# ---------------------------------------------------------------------------

class TestWorkbenchSubmit:
    def _mock_response(self, task_id: str = "task-123"):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"id": task_id}
        return resp

    def test_submit_without_validate_raises(self):
        wb = Workbench()
        with pytest.raises(ValueError):
            wb.submit()

    def test_submit_without_build_tes_raises(self):
        wb = Workbench()
        wb.validate(**VALID_KWARGS)
        with pytest.raises(ValueError, match="build_tes"):
            wb.submit()

    def test_submit_returns_task_id(self):
        wb = Workbench()
        wb.validate(**VALID_KWARGS).build_tes(**VALID_TES_PARAMS)

        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            return_value=self._mock_response("task-456"),
        ):
            task_id = wb.submit()

        assert task_id == "task-456"

    def test_full_chain_validate_build_submit(self):
        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            return_value=self._mock_response("task-789"),
        ):
            task_id = (
                Workbench()
                .validate(**VALID_KWARGS)
                .build_tes(**VALID_TES_PARAMS)
                .submit()
            )

        assert task_id == "task-789"

    def test_submit_posts_to_tes_endpoint(self):
        wb = Workbench()
        wb.validate(**VALID_KWARGS).build_tes(**VALID_TES_PARAMS)

        with patch(
            "five_safes_tes_workbench.core.submit_builder.requests.post",
            return_value=self._mock_response(),
        ) as mock_post:
            wb.submit()

        posted_url = mock_post.call_args[0][0]
        assert posted_url.startswith("https://tes.example.com")
        assert posted_url.endswith("/v1/tasks")
