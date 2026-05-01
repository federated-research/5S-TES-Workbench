from ....common.exceptions.tes_error import TESBuildError
from ....common.params.custom_template_params import CustomUserParams
from ....common.params.tes_builder_params import (
    ExecutorTESParams,
    InputTESParams,
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
        required_fields = ("name", "executors")
        missing = [field for field in required_fields if field not in overrides]
        if missing:
            raise TESBuildError(
                f"Custom template missing required fields: {missing}. "
                "name and executors are required."
            )

        # ---- Defaults for optional fields ----
        _DESCRIPTION = overrides.get("description", "Custom TES Task")

        # ---- Pull caller-provided values ----
        _NAME = overrides["name"]
        _EXECUTORS = overrides["executors"]
        _OUTPUTS = overrides.get(
            "outputs",
            [],
        )
        _INPUTS = overrides.get(
            "inputs",
            [],
        )

        return TESTaskParams(
            name=_NAME,
            description=_DESCRIPTION,
            executors=[
                ExecutorTESParams(
                    executor_image=executor["executor_image"],
                    executor_command=executor["executor_command"],
                    executor_workdir=executor.get("executor_workdir", None),
                    executor_stdin=executor.get("executor_stdin", None),
                    executor_stdout=executor.get("executor_stdout", None),
                    executor_stderr=executor.get("executor_stderr", None),
                    executor_env=executor.get("executor_env", None),
                    executor_ignore_error=executor.get("executor_ignore_error", None),
                )
                for executor in _EXECUTORS
            ],
            outputs=[
                OutputTESParams(
                    output_name=output.get("output_name", "Output"),
                    output_description=output.get(
                        "output_description", "Output results"
                    ),
                    output_url=output.get("output_url", "s3://"),
                    output_path=output.get("output_path", "/outputs"),
                    output_type=output.get("output_type", "DIRECTORY"),
                    output_path_prefix=output.get("output_path_prefix", None),
                )
                for output in _OUTPUTS
            ],
            inputs=[
                InputTESParams(
                    input_name=input.get("input_name", None),
                    input_description=input.get("input_description", None),
                    input_url=input.get("input_url", None),
                    input_path=input["input_path"],
                    input_type=input.get("input_type", None),
                    input_content=input.get("input_content", None),
                    input_streamable=input.get("input_streamable", None),
                )
                for input in _INPUTS
            ],
        )
