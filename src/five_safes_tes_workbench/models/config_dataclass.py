from dataclasses import dataclass
from typing import Final
from ..enums.config_enums import ConfigKey


@dataclass(frozen=True)
class ConfigValidationDataClass:
    """
    Data class representing the configuration for 
    validating the Five Safes TES Workbench setup. 

    Attributes:
    ----------
        project (str): The name of the project to validate.
        tes_base_url (str): The base URL of the TES service.
        minio_sts_endpoint (str): The endpoint for MinIO STS (Security Token Service).
        minio_endpoint (str): The endpoint for MinIO.
        minio_output_bucket (str): The name of the MinIO bucket for output.
        tres (Tuple[str, ...]): A tuple of TES endpoints to validate against.
    """

    project: str
    tes_base_url: str
    minio_sts_endpoint: str
    minio_endpoint: str
    minio_output_bucket: str
    tres: tuple[str, ...]


# // ----- KEY MAP FOR FILE LOADING -----

"""
Mapping of expected keys in the configuration file to the
field names when loading the path from the file. 
"""
FILE_KEY_MAP: Final[dict[str, str]] = {
    "5STES_PROJECT": ConfigKey.PROJECT.value,
    "TES_BASE_URL": ConfigKey.TES_BASE_URL.value,
    "MINIO_STS_ENDPOINT": ConfigKey.MINIO_STS_ENDPOINT.value,
    "MINIO_ENDPOINT": ConfigKey.MINIO_ENDPOINT.value,
    "MINIO_OUTPUT_BUCKET": ConfigKey.MINIO_OUTPUT_BUCKET.value,
    "5STES_TRES": ConfigKey.TRES.value,
}