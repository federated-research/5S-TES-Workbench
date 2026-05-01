from ....common.params.helloworld_params import HelloWorldUserParams
from ....common.params.tes_builder_params import (
    ExecutorTESParams,
    OutputTESParams,
    TESTaskParams,
)
from ...base.tes_template_abc import BaseTESTemplate


class HelloWorldTemplate(BaseTESTemplate[HelloWorldUserParams]):
    """
    "Hello World" template for TES tasks.

    Method Usage:
    - `build_tes.hello_world(name=..., description=..., image=..., command=...)`
    """

    @property
    def name(self) -> str:
        """Unique name for this template."""
        return "hello_world"

    def resolve(self, overrides: HelloWorldUserParams) -> TESTaskParams:
        """Merges user-provided params with internal defaults."""

        _NAME = overrides.get("name", "Hello World Task")
        _DESCRIPTION = overrides.get("description", "Hello World")
        _IMAGE = overrides.get("image", "alpine:latest")
        _COMMAND = overrides.get("command", ["echo", "hello world"])
        _OUTPUT_URL = overrides.get("output_url", "s3://")
        _OUTPUT_PATH = overrides.get("output_path", "/outputs")
        _OUTPUT_STDOUT = _OUTPUT_PATH + "/stdout.txt"

        return TESTaskParams(
            name=_NAME,
            description=_DESCRIPTION,
            executors=[
                ExecutorTESParams(
                    image=_IMAGE,
                    command=_COMMAND,
                    workdir=_OUTPUT_PATH,
                    stdout=_OUTPUT_STDOUT,
                )
            ],
            outputs=[
                OutputTESParams(
                    name="Stdout",
                    description="Stdout results",
                    url=_OUTPUT_URL,
                    path=_OUTPUT_PATH,
                )
            ],
        )
