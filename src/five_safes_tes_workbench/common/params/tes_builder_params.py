from typing import Literal

from pydantic import BaseModel


class InputTESParams(BaseModel):
    name: str | None = None
    description: str | None = None
    url: str | None = None
    path: str
    type: Literal["FILE", "DIRECTORY"] | None = None
    content: str | None = None
    streamable: bool | None = None


class OutputTESParams(BaseModel):
    name: str | None = None
    description: str | None = None
    url: str
    path: str
    type: Literal["FILE", "DIRECTORY"] | None = None
    path_prefix: str | None = None


class ExecutorTESParams(BaseModel):
    image: str
    command: list[str]
    workdir: str | None = None
    stdin: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    env: dict[str, str] | None = None
    ignore_error: bool | None = None


class TESTaskParams(BaseModel):
    """
    Parameters for building a TES task
    """

    name: str
    executors: list[ExecutorTESParams]
    description: str | None = None
    inputs: list[InputTESParams] | None = None
    outputs: list[OutputTESParams] | None = None
    volumes: list[str] | None = None
