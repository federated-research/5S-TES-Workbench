from typing import NotRequired, Required, TypedDict


class InputTESParams(TypedDict):
    input_name: NotRequired[str | None]
    input_description: NotRequired[str | None]
    input_url: NotRequired[str | None]
    input_path: Required[str]
    input_type: NotRequired[str]
    input_content: NotRequired[str | None]
    input_streamable: NotRequired[bool | None]


class OutputTESParams(TypedDict):
    output_name: NotRequired[str]
    output_description: NotRequired[str]
    output_type: NotRequired[str]
    output_url: Required[str]
    output_path: Required[str]
    output_path_prefix: NotRequired[str | None]


class ExecutorTESParams(TypedDict):
    executor_image: Required[str]
    executor_command: Required[list[str]]
    executor_workdir: NotRequired[str | None]
    executor_stdin: NotRequired[str | None]
    executor_stdout: NotRequired[str | None]
    executor_stderr: NotRequired[str | None]
    executor_env: NotRequired[dict[str, str] | None]
    executor_ignore_error: NotRequired[bool | None]


class TESTaskParams(TypedDict):
    """
    Parameters for building a TES task
    """

    name: Required[str]
    executors: Required[list[ExecutorTESParams]]
    description: NotRequired[str]
    inputs: NotRequired[list[InputTESParams] | None]
    outputs: NotRequired[list[OutputTESParams] | None]
    volumes: NotRequired[list[str] | None]
