from typing import NotRequired, Required, TypedDict


class InputTESParams(TypedDict):
    name: NotRequired[str | None]
    description: NotRequired[str | None]
    url: NotRequired[str | None]
    path: Required[str]
    type: NotRequired[str]
    content: NotRequired[str | None]
    streamable: NotRequired[bool | None]


class OutputTESParams(TypedDict):
    name: NotRequired[str]
    description: NotRequired[str]
    type: NotRequired[str]
    url: Required[str]
    path: Required[str]
    path_prefix: NotRequired[str | None]


class ExecutorTESParams(TypedDict):
    image: Required[str]
    command: Required[list[str]]
    workdir: NotRequired[str | None]
    stdin: NotRequired[str | None]
    stdout: NotRequired[str | None]
    stderr: NotRequired[str | None]
    env: NotRequired[dict[str, str] | None]
    ignore_error: NotRequired[bool | None]


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
