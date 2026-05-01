from typing import NotRequired, Required, TypedDict

from five_safes_tes_workbench.common.params.tes_builder_params import (
    ExecutorTESParams,
    InputTESParams,
    OutputTESParams,
)


class CustomUserParams(TypedDict):
    """
    User-facing parameters for the Custom template.

    - name: Task name.
    - description: Task description.
    - image: Container image to run.
    - command: Command to execute in the container.
    - output_url: S3 output URL.
    - output_path: Output path inside the container.
    """

    name: Required[str]
    executors: Required[list[ExecutorTESParams]]
    description: NotRequired[str]
    inputs: NotRequired[list[InputTESParams]]
    outputs: NotRequired[list[OutputTESParams]]
    volumes: NotRequired[list[str]]
