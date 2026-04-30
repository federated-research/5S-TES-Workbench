from typing import NotRequired, Required, TypedDict


class InputTESParams(TypedDict):
    input_name: NotRequired[str]
    input_description: NotRequired[str]
    input_url: NotRequired[str]
    input_path: Required[str]
    input_type: NotRequired[str]
    input_content: NotRequired[str]
    input_streamable: NotRequired[bool]


class OutputTESParams(TypedDict):
    output_name: NotRequired[str]
    output_description: NotRequired[str]
    output_type: NotRequired[str]
    output_url: Required[str]
    output_path: Required[str]
    output_path_prefix: NotRequired[str]


class ExecutorTESParams(TypedDict):
    executor_image: Required[str]
    executor_command: Required[list[str]]
    executor_workdir: NotRequired[str]
    executor_stdin: NotRequired[str]
    executor_stdout: NotRequired[str]
    executor_stderr: NotRequired[str]
    executor_env: NotRequired[dict[str, str]]
    executor_ignore_error: NotRequired[bool]


class TESTaskParams(TypedDict):
    """
    Parameters for building a TES task
    """

    name: Required[str]
    executors: Required[list[ExecutorTESParams]]
    description: NotRequired[str]
    inputs: NotRequired[list[InputTESParams]]
    outputs: NotRequired[list[OutputTESParams]]
    volumes: NotRequired[list[str]]
