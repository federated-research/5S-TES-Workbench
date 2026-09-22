"""Builder responsible for fetching task results from S3 after submission."""

from pathlib import Path
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

from five_safes_tes_workbench.helpers.project_s3_info import ProjectS3Info

from ...constants.s3 import S3_REGION
from ...helpers.auth import resolve_sts_bearer
from ...helpers.s3 import (
    download_result,
    list_results,
)
from ...helpers.token import exchange_s3_token
from ...schema.auth_schema import AuthValidationModel
from ...schema.config_schema import ConfigValidationModel
from ...utils.logger import get_logger

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

logger = get_logger(__name__)


class MinioClientBuilder:
    """
    Builder responsible for connecting to project S3 storage and retrieving
    task output objects after a TES task has completed.

    Credentials are obtained by exchanging the bearer token at the
    configured STS endpoint (AssumeRoleWithWebIdentity). The data-plane
    client is boto3, which speaks the same S3 API as MinIO and RustFS.
    """

    def __init__(
        self,
        config: ConfigValidationModel,
        auth: AuthValidationModel,
        project_s3_info: ProjectS3Info,
    ) -> None:
        """
        Exchange the bearer token for temporary S3 credentials via STS
        and create an authenticated boto3 S3 client.

        Parameters
        ----------
        - config: Validated infrastructure configuration.
        - auth: Validated authentication details used to obtain the bearer
          token.
        - project_s3_info: Project S3 info for the project.
        """
        bearer = resolve_sts_bearer(auth)
        credentials = exchange_s3_token(bearer, project_s3_info.api_endpoint)
        self._client: "S3Client" = boto3.client(  # pyright: ignore[reportAttributeAccessIssue]
            "s3",
            endpoint_url=project_s3_info.api_endpoint,
            aws_access_key_id=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_session_token=credentials.session_token,
            region_name=S3_REGION,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )
        self._config = config
        logger.info(
            "S3 client initialized (endpoint=%s)",
            project_s3_info.api_endpoint,
        )

    def download_results(
        self,
        task_id: str,
        output_dir: Path,
        bucket: str,
    ) -> list[Path]:
        """
        Download all output objects for a task to a local directory.

        Each object is written to ``output_dir/<filename>``, stripping the
        leading ``<task_id>/`` prefix used as a folder separator.

        Parameters
        ----------
        - task_id: ID returned by the TES submission.
        - output_dir: Local directory to write the downloaded files into.
          The directory (and any missing parents) is created automatically.
        - bucket: Output bucket for the project.

        Returns
        -------
        List of :class:`~pathlib.Path` objects pointing to every downloaded
        file.
        """
        object_paths = list_results(self._client, task_id, bucket)

        downloaded: list[Path] = []
        for path in object_paths:
            logger.info("Downloading result object: %s", path)
            local_path = download_result(self._client, path, output_dir, bucket)
            downloaded.append(local_path)

        return downloaded
