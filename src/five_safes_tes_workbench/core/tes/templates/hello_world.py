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

        _DESCRIPTION = overrides.get("description", "Hello World")
        _OUTPUT_URL = overrides.get("output_url", "s3://hello-world-output")
        _OUTPUT_PATH = overrides.get("output_path", "/outputs")

        return TESTaskParams(
            # --- Required params from user ---
            name=overrides["name"],
            image=overrides["image"],
            command=overrides["command"],

            # --- Optional params with template defaults ---
            description=_DESCRIPTION,
            output_url=_OUTPUT_URL,
            output_path=_OUTPUT_PATH,
        )
