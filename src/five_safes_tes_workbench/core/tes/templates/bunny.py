from ....common.exceptions.tes_error import TESBuildError
from ....common.params.bunny_params import BunnyUserParams
from ....common.params.tes_builder_params import (
    ExecutorTESParams,
    OutputTESParams,
    TESTaskParams,
)
from ...base.tes_template_abc import BaseTESTemplate


class BunnyTemplate(BaseTESTemplate[BunnyUserParams]):
    """
    Bunny CLI template for TES tasks.

    Runs the Health Informatics Bunny CLI container with
    user-provided command arguments.

    Method Usage:
    -------------
        build_tes.bunny(
            name="Bunny task",
            command=["--body-json", "{...}", "--output", "/outputs/output.json"],
        )
    """

    # ---- Internal defaults ----
    _DEFAULT_IMAGE = (
        "ghcr.io/health-informatics-uon/five-safes-tes-analytics-bunny-cli:1.6.0"
    )
    _DEFAULT_OUTPUT_URL = "s3://"
    _DEFAULT_OUTPUT_PATH = "/outputs"
    _DEFAULT_DESCRIPTION = "Bunny CLI analytics task"

    @property
    def name(self) -> str:
        """
        Unique name for this template.
        """
        return "bunny"

    def resolve(self, overrides: BunnyUserParams) -> TESTaskParams:
        """
        Merges user-provided params with internal defaults.
        Raises TESBuildError if required fields are missing.
        """

        # ---- Validate required fields ----
        required_fields = ("name", "command")
        missing = [f for f in required_fields if f not in overrides]
        if missing:
            raise TESBuildError(
                f"Bunny template missing required fields: {missing}. "
                "Both 'name' and 'command' are required."
            )

        # ---- Resolve params (user overrides win) ----
        _NAME = overrides["name"]
        _COMMAND = overrides["command"]
        _DESCRIPTION = overrides.get("description", self._DEFAULT_DESCRIPTION)
        _IMAGE = overrides.get("image", self._DEFAULT_IMAGE)
        _OUTPUT_URL = overrides.get("output_url", self._DEFAULT_OUTPUT_URL)
        _OUTPUT_PATH = overrides.get("output_path", self._DEFAULT_OUTPUT_PATH)

        return TESTaskParams(
            name=_NAME,
            description=_DESCRIPTION,
            executors=[
                ExecutorTESParams(
                    executor_image=_IMAGE,
                    executor_command=_COMMAND,
                )
            ],
            outputs=[
                OutputTESParams(
                    output_name="Query Results",
                    output_description="Results from the requested query execution",
                    output_url=_OUTPUT_URL,
                    output_path=_OUTPUT_PATH,
                    output_type="DIRECTORY",
                )
            ],
        )
