from typing import Protocol, Unpack

from ...common.params.validate_params import ConfigValidationParams
from ...schema.auth_schema import AuthValidationModel
from ...schema.config_schema import ConfigValidationModel


class ValidatorProtocol(Protocol):
    """
    Protocol for configuration and authentication validation.

    Any class that implements this protocol must provide:
        - `config` property: Returns validated config.
        - `auth` property: Returns validated auth.
        - `validate()`: Validates config and auth from 
           YAML or keyword arguments.
    """

    @property
    def config(self) -> ConfigValidationModel: ...

    @property
    def auth(self) -> AuthValidationModel: ...

    def validate(
        self,
        config_path: str | None = None,
        **kwargs: Unpack[ConfigValidationParams],
    ) -> None: ...