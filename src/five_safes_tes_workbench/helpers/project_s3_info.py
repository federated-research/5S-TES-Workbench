from dataclasses import dataclass
from urllib.parse import urljoin

import requests

from five_safes_tes_workbench.schema.config_schema import ConfigValidationModel
from five_safes_tes_workbench.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectS3Info:
    """
    Information about a project S3 info.

    Attributes:
    -----------
    - output_bucket: The S3 bucket for the project.
    - api_endpoint: The S3 API URL for the project.
    """

    output_bucket: str
    api_endpoint: str


def get_project_s3_info(project_name: str, config: ConfigValidationModel) -> ProjectS3Info:
    """
    Get the project S3 info for a given project.
    """
    project_s3_info_url = urljoin(
        config.tes_base_url,
        f"api/Project/GetProjectS3Info?projectName={project_name}",
    )
    response = requests.get(
        project_s3_info_url,
        timeout=60,
    )
    response.raise_for_status()

    project_s3_info = response.json()
    if project_s3_info is None:
        raise RuntimeError(f"No project S3 info found for project {project_name}")
    return ProjectS3Info(
        output_bucket=project_s3_info["outputBucket"],
        api_endpoint=project_s3_info["apiUrl"],
    )
