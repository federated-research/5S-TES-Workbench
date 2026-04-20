from ...schema.config_schema import WorkbenchConfigValidationModel
from ...models.config_dataclass import ConfigValidationDataClass

class ConfigValidator:
    """
    Validator for Five Safes TES Workbench configuration.
    """

    def __init__(self, config_data: dict[str, str | list[str]]) -> None:
        """
        Initialize the validator with raw config data.

        Attributes:
        -----------
            config_data: Dictionary of configuration
            key-value pairs.
        """
        self._config_data = config_data

    def validate(self) -> ConfigValidationDataClass:
        """
        Validate configuration data and return immutable config.

        Returns:
        ---------
            ConfigValidationDataClass: Validated, frozen configuration.

        Raises:
        --------
            pydantic.ValidationError: If any field is invalid or missing.
            ValueError: If config_data is empty.
        """

        validated = WorkbenchConfigValidationModel.model_validate(self._config_data)

        return ConfigValidationDataClass(
            project=validated.project,
            tes_base_url=validated.tes_base_url,
            minio_sts_endpoint=validated.minio_sts_endpoint,
            minio_endpoint=validated.minio_endpoint,
            minio_output_bucket=validated.minio_output_bucket,
            tres=tuple(validated.tres),
        )