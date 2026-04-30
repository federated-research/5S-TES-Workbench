from ....common.params.custom_template_params import CustomUserParams
from ....common.params.tes_builder_params import TESTaskParams
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
        """
        return TESTaskParams(
            name=overrides["name"],
            description=overrides["description"],
            image=overrides["image"],
            command=overrides["command"],
            output_url=overrides["output_url"],
            output_path=overrides["output_path"],
        )
