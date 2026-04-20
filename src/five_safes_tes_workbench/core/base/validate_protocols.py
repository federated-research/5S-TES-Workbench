from typing import Protocol

from ...models.config_dataclass import ConfigValidationDataClass

# // ----- CONFIG VALIDATOR PROTOCOLS -----

class ConfigValidatorProtocols(Protocol):
    """
    Protocol for configuration validators.
    """

    def validate(self) -> ConfigValidationDataClass:
        """
        Validate and return immutable config.
        """
        ...


# // ----- CONFIG LOADER PROTOCOLS -----

class ConfigLoaderProtocol(Protocol):
    """
    Protocol for configuration loaders.

    Any class that implements a load() method returning
    a dict of config data satisfies this protocol.
    """

    def load(self) -> dict[str, str | list[str]]:
        """
        Load configuration from a source.

        Returns:
            Dictionary with field names as keys.
        """
        ...
