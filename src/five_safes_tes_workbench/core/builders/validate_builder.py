from typing import Unpack

from ...common.enums.validator_enums import AuthMode
from ...common.exceptions.auth_errors import AuthValidationError
from ...common.exceptions.config_errors import ConfigValidationError
from ...common.params.validate_params import ConfigValidationParams, split_config_params
from ...schema.auth_schema import AuthValidationModel
from ...schema.config_schema import ConfigValidationModel
from ...schema.validation_schema import WorkbenchValidationModel
from ...utils.logger import get_logger

logger = get_logger(__name__)


class WorkbenchValidateBuilder():
    """
    Builder class responsible for validating configuration
    and authentication parameters for the TES workbench.
    """

    def __init__(self) -> None:
        """
        Initializes the WorkbenchValidateBuilder
        with placeholders for config and auth
        parameters that will be populated
        during validation.

        Attributes:
        -----------
        - _config: Holds the validated infrastructure configuration.
        - _auth: Holds the validated authentication configuration.
        """
        self._config: ConfigValidationModel | None = None
        self._auth: AuthValidationModel | None = None

    @property
    def config(self) -> ConfigValidationModel:
        """
        Returns the validated infrastructure configuration.
        """
        if self._config is None:
            raise ConfigValidationError([
                "No config information found. "
                "Please call validate() before building the TES message."
            ])
        return self._config


    @property
    def auth(self) -> AuthValidationModel:
        """
        Returns the validated authentication configuration.
        """
        if self._auth is None:
            raise AuthValidationError([
                "No auth information found. "
                "Please call validate() before submitting the TES message."
            ])
        return self._auth

    def validate(
        self,
        config_path: str | None = None,
        **kwargs: Unpack[ConfigValidationParams],
    ) -> None:
        """
        Validates the configuration and authentication
        parameters for the TES workbench.

        This method supports two modes of input:
        1. YAML File Input: Provide a path to a YAML file
           containing the configuration and authentication details.

        2. Direct Parameter Input: Provide the configuration and
           authentication details directly as keyword arguments.

        Attributes:
        -----------
        - config_path: Optional path to a YAML configuration file.

        - kwargs: Keyword arguments for direct parameter input. The
        ConfigValidationParams holds the expected params for both
        config and auth validation.
        """

        if config_path is not None:
            model = WorkbenchValidationModel.from_yaml(config_path)

        else:
            config, auth = split_config_params(kwargs)  # type: ignore[arg-type]
            model = WorkbenchValidationModel.model_validate(
                {
                    "config": config,
                    "auth": auth,
                }
            )

        self._config = model.config
        self._auth = model.auth

        logger.info("Validation successful")
        logger.info("Config: %s", self._config)
        logger.info("Auth mode: %s", self._auth.auth_mode)

        if self._auth.auth_mode == AuthMode.ACCESS_TOKEN:
            logger.info("Access Token: %s", self._auth.access_token)
        else:
            logger.info("Auth: %s", self._auth)
