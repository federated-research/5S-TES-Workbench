from five_safes_tes_workbench.workbench import Workbench  # type: ignore

# ---------------------------------------------------------------------------
# test data
# ---------------------------------------------------------------------------

VALID_KWARGS = {
    "project": "my-project",
    "tes_base_url": "https://tes.example.com",
    "tres": ["TRE-A"],
    "access_token": "tok-abc123",
}


class TestWorkbenchInit:
    def test_instantiates_without_error(self):
        wb = Workbench()
        assert wb is not None

    def test_has_validator_task_builder_and_submitter(self):
        wb = Workbench()
        assert hasattr(wb, "_validator")
        assert hasattr(wb, "_task_builder")
        assert hasattr(wb, "_submitter")

    def test_validate_returns_self_for_chaining(self):
        wb = Workbench()
        result = wb.validate(**VALID_KWARGS)
        assert result is wb
