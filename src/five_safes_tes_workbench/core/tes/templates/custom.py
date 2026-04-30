from ....common.exceptions.tes_error import TESBuildError
from ....common.params.custom_template_params import CustomUserParams
from ....common.params.tes_builder_params import (
    ExecutorTESParams,
    OutputTESParams,
    TESTaskParams,
)
from ...base.tes_template_abc import BaseTESTemplate


class CustomTemplate(BaseTESTemplate[CustomUserParams]):
    """
    Fully custom TES task template with no internal defaults.
    All parameters must be provided by the caller.

    Method Usage:
    -------------
    - `build_tes.custom(name=..., description=..., image=...,
                        command=..., output_url=..., output_path=...)`
    """

    @property
    def name(self) -> str:
        """
        Unique name for this template.
        """
        return "custom"

    def resolve(self, overrides: CustomUserParams) -> TESTaskParams:
        """
        Returns a TESTaskParams built entirely from the caller's params.
        Raises TESBuildError if any required field is missing.
        """

        # ---- Validate required user inputs ----
        required_fields = ("name", "image", "command")
        missing = [field for field in required_fields if field not in overrides]
        if missing:
            raise TESBuildError(
                f"Custom template missing required fields: {missing}. "
                "name, image, and command are required."
            )

        # ---- Defaults for optional fields ----
        _OUTPUT_URL = overrides.get("output_url", "s3://output")
        _OUTPUT_PATH = overrides.get("output_path", "/outputs")
        _DESCRIPTION = overrides.get("description", "Custom TES Task")

        # ---- Pull caller-provided values ----
        _NAME = overrides["name"]
        _IMAGE = overrides["image"]
        _COMMAND = overrides["command"]

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
                    output_name="Stdout",
                    output_description="Stdout results",
                    output_url=_OUTPUT_URL,
                    output_path=_OUTPUT_PATH,
                )
            ],
        )
