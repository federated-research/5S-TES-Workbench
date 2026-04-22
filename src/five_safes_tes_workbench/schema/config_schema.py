from typing import Annotated
from pydantic import BaseModel, field_validator, ValidationInfo, AnyHttpUrl, BeforeValidator
from ..common.validator_enums import ConfigKey
from ..common.validator_dataclass import ConfigValidationDataModel


HttpUrlString = Annotated[str, BeforeValidator(lambda v: str(AnyHttpUrl(v)))]

class ConfigValidationModel(BaseModel):
    """
    Pydantic Model for validating the configuration of
    the Five Safes TES Workbench setup.

    Attributes:
    -----------
    - project: The name of the project to validate.
    - tes_base_url: The base URL of the TES service.
    - minio_sts_endpoint: The endpoint for MinIO STS.
    - minio_endpoint: The endpoint for MinIO.
    - minio_output_bucket: The name of the MinIO bucket for output.
    - tres: A list of TREs.
    """

    project: str
    tes_base_url: HttpUrlString
    minio_sts_endpoint: HttpUrlString
    minio_endpoint: str
    minio_output_bucket: str
    tres: list[str] 

    @field_validator(
        ConfigKey.PROJECT.value,
        ConfigKey.TES_BASE_URL.value,
        ConfigKey.MINIO_STS_ENDPOINT.value,
        ConfigKey.MINIO_ENDPOINT.value,
        ConfigKey.MINIO_OUTPUT_BUCKET.value,
        mode="before"
    )
    @classmethod
    def check_not_empty(cls, v: str, info: ValidationInfo) -> str:
        if not v or not v.strip():
            raise ValueError(f"'{info.field_name}' must not be empty")
        return v.strip()
    

    @field_validator(ConfigKey.TRES.value)
    @classmethod
    def check_tres_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Must have at least one 'TRE'. ")
        cleaned = [item.strip() for item in v]
        for i, item in enumerate(cleaned):
            if not item:
                raise ValueError(
                    f"'tres' contains an empty value at index {i}"
                )
        return cleaned
    
    # Return Configs as Immutable Dataclass
    
    def to_validated_config(self) -> ConfigValidationDataModel:
        """
        Convert the validated Pydantic model to a 
        frozen dataclass.

        Returns:
        ---------
            ConfigValidationDataModel: An immutable 
            configuration dataclass.
        """
        return ConfigValidationDataModel(
            project=self.project,
            tes_base_url=self.tes_base_url,
            minio_sts_endpoint=self.minio_sts_endpoint,
            minio_endpoint=self.minio_endpoint,
            minio_output_bucket=self.minio_output_bucket,
            tres=tuple(self.tres),
        )


