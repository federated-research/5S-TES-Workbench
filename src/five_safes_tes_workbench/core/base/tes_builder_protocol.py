from typing import Protocol

import tes  # type: ignore

from ...common.params.tes_builder_params import TESTaskParams
from ...schema.config_schema import ConfigValidationModel


class TESBuilderProtocol(Protocol):
    """
    Protocol for building TES tasks.

    Any class that implements this protocol must provide:
        - `tes_task` property: Returns the constructed TES task.
        - `build()`: Builds a TES task from config and params.
    """

    @property
    def tes_task(self) -> tes.Task: ...

    def build(
        self,
        config: ConfigValidationModel,
        params: TESTaskParams,
    ) -> None: ...