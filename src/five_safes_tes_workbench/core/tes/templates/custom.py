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
        for i, input in enumerate(_INPUTS):
            if "path" not in input:
                raise TESBuildError(
                    f"inputs[{i}] is missing required field 'path'. "
                    "path is required for every input entry."
                )

        # ---- Validate outputs: output_path and output_url are required per entry ----
        for i, output in enumerate(_OUTPUTS):
            missing_output_fields = [
                field for field in ("path", "url") if field not in output
            ]
            if missing_output_fields:
                raise TESBuildError(
                    f"outputs[{i}] is missing required fields: "
                    f"{missing_output_fields}. "
                    "path and url are required for every output entry."
                )

        return TESTaskParams(
            name=_NAME,
            description=_DESCRIPTION,
            executors=[
                ExecutorTESParams(
                    image=executor["image"],
                    command=executor["command"],
                    workdir=executor.get("workdir", None),
                    stdin=executor.get("stdin", None),
                    stdout=executor.get("stdout", None),
                    stderr=executor.get("stderr", None),
                    env=executor.get("env", None),
                    ignore_error=executor.get("ignore_error", None),
                )
                for executor in _EXECUTORS
            ],
            outputs=[
                OutputTESParams(
                    name=output.get("name", "Output"),
                    description=output.get("description", "Output results"),
                    url=output["url"],
                    path=output["path"],
                    type=output.get("type", "DIRECTORY"),
                    path_prefix=output.get("path_prefix", None),
                )
                for output in _OUTPUTS
            ],
            inputs=[
                InputTESParams(
                    name=input.get("name", None),
                    description=input.get("description", None),
                    url=input.get("url", None),
                    path=input["path"],
                    type=input.get("type", "DIRECTORY"),
                    content=input.get("content", None),
                    streamable=input.get("streamable", None),
                )
                for input in _INPUTS
            ],
            volumes=_VOLUMES,
        )
