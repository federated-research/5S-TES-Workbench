from typing import Annotated

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    BeforeValidator,
    ValidationInfo,
    field_validator,
)

from ..common.enums.validator_enums import ConfigParamEnums
from ..common.exceptions.config_errors import ConfigValidationError

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

    model_config = {"frozen": True}

    project: str
    tes_base_url: HttpUrlString
    minio_sts_endpoint: HttpUrlString
    minio_endpoint: HttpUrlString
    minio_output_bucket: str
    tres: list[str]

    @field_validator(
        *[e.value for e in ConfigParamEnums if e != ConfigParamEnums.TRES],
        mode="before",
    )
    @classmethod
    def check_not_empty(cls, v: str, info: ValidationInfo) -> str:
        if not v or not v.strip():
            raise ConfigValidationError([f"'{info.field_name}' must not be empty."])
        return v.strip()

    @field_validator(ConfigParamEnums.TRES.value)
    @classmethod
    def check_tres_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ConfigValidationError(["Must have at least one 'TRE'."])

        cleaned = [item.strip() for item in v]
        for i, item in enumerate(cleaned):
            if not item:
                raise ValueError(f"'tres' contains an empty value at index {i}")
        return cleaned
