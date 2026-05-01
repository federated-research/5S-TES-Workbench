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

        # ---- Validate always-required top-level fields ----
        required_fields = ("name", "executors")
        missing = [field for field in required_fields if field not in overrides]
        if missing:
            raise TESBuildError(
                f"Custom template missing required fields: {missing}. "
                "name and executors are required."
            )

        # ---- Pull caller-provided values with defaults ----
        _DESCRIPTION = overrides.get("description", "Custom TES Task")
        _VOLUMES = overrides.get("volumes", [])
        _NAME = overrides["name"]
        _EXECUTORS = overrides["executors"]
        _OUTPUTS = overrides.get("outputs", [])
        _INPUTS = overrides.get("inputs", [])

        # ---- Validate inputs: input_path is required per entry ----
        for i, inp in enumerate(_INPUTS):
            if "input_path" not in inp:
                raise TESBuildError(
                    f"inputs[{i}] is missing required field 'input_path'. "
                    "input_path is required for every input entry."
                )

        # ---- Validate outputs: output_path and output_url are required per entry ----
        for i, out in enumerate(_OUTPUTS):
            missing_output = [
                field for field in ("output_path", "output_url") if field not in out
            ]
            if missing_output:
                raise TESBuildError(
                    f"outputs[{i}] is missing required fields: {missing_output}. "
                    "output_path and output_url are required for every output entry."
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
                    output_url=output["output_url"],
                    output_path=output["output_path"],
                    output_type=output.get("output_type", "DIRECTORY"),
                    output_path_prefix=output.get("output_path_prefix", None),
                )
                for output in _OUTPUTS
            ],
            inputs=[
                InputTESParams(
                    input_name=inp.get("input_name", None),
                    input_description=inp.get("input_description", None),
                    input_url=inp.get("input_url", None),
                    input_path=inp["input_path"],
                    input_type=inp.get("input_type", "DIRECTORY"),
                    input_content=inp.get("input_content", None),
                    input_streamable=inp.get("input_streamable", None),
                )
                for inp in _INPUTS
            ],
            volumes=_VOLUMES,
        )
