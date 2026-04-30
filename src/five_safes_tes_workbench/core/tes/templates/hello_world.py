from ....common.params.helloworld_params import HelloWorldUserParams
from ....common.params.tes_builder_params import TESTaskParams
from ...base.tes_template_abc import BaseTESTemplate


class HelloWorldTemplate(BaseTESTemplate[HelloWorldUserParams]):
    """
    "Hello World" template for TES tasks.

    Method Usage:
    - `build_tes.hello_world(name=..., description=..., image=...)`
    """

    @property
    def name(self) -> str:
        """
        Unique name for this template.
        """
        return "hello_world"

    def resolve(self, overrides: HelloWorldUserParams) -> TESTaskParams:
        """
        Merges user-provided params with internal defaults.
        """

        # ---- Fixed parameters for this template ----

        _NAME = overrides.get("name", "Hello World Task")
        _IMAGE = overrides.get("image", "alpine:latest")
        _COMMAND = overrides.get("command", ["echo", "hello world"])
        _DESCRIPTION = overrides.get("description", "Hello World")
        _OUTPUT_URL = overrides.get("output_url", "s3://hello-world-output")
        _OUTPUT_PATH = overrides.get("output_path", "/outputs")

        return TESTaskParams(

            name=_NAME,
            image=_IMAGE,
            command=_COMMAND,
            description=_DESCRIPTION,
            output_url=_OUTPUT_URL,
            output_path=_OUTPUT_PATH,
        )
