from typing import Unpack

from .core.validate_builder import WorkbenchValidateBuilder
from .core.tes_builder import WorkbenchTESBuilder
from .core.submit_builder import WorkbenchSubmitBuilder
from .common.validate_params import ConfigValidationParams
from .common.tes_builder_params import TESTaskParams


class Workbench:
    """
    Main class for the Five Safes TES Workbench.

    Process
    -------
    This class holds the main methods as follows:

    1. validate: Validates the configuration.
    2. build_tes: Builds the TES task.
    3. submit: Submits the TES task to the endpoint.
    """

    def __init__(self) -> None:
        """
        Initializes the Workbench with instances of the
        validate builder, TES builder, and submit builder.
        """
        self._validator = WorkbenchValidateBuilder()
        self._task_builder = WorkbenchTESBuilder()
        self._submitter = WorkbenchSubmitBuilder()

    # ----- Validation Builder -----

    def validate(
        self,
        config_path: str | None = None,
        **kwargs: Unpack[ConfigValidationParams],
    ) -> "Workbench":
        """
        Validates the configuration and
        authentication parameters.

        Parameters
        ----------
        - config_path: Optional path to the configuration file.
        - kwargs: Parameters for validation.
        """
        self._validator.validate(config_path, **kwargs)
        return self
    
    # ----- TES Builder -----

    def build_tes(self, **kwargs: Unpack[TESTaskParams]) -> "Workbench":
        """ 
        Builds the TES message and provided TES 
        task parameters.
        
        Parameters
        ----------
        - kwargs: Parameters for building the TES task.
        """
        self._task_builder.build(
            self._validator.config,
            kwargs,
        )
        return self

    # ----- Submit Builder -----

    def submit(self) -> str:
        """ 
        Submits the built TES task to the 
        configured TES endpoint.
        """
        return self._submitter.submit(
            config=self._validator.config,
            auth=self._validator.auth,
            task=self._task_builder.tes_task,
        )
