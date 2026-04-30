"""Builder responsible for fetching task results from MinIO after submission."""

from pathlib import Path

from minio import Minio

from ..helpers.auth import resolve_bearer
from ..helpers.minio import (
    download_result,
    exchange_minio_token,
    list_results,
)
from ..helpers.url import is_https, strip_scheme
from ..schema.auth_schema import AuthValidationModel
from ..schema.config_schema import ConfigValidationModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MinioClientBuilder:
    """
    Builder responsible for connecting to MinIO and retrieving task
    output objects after a TES task has completed.

    Credentials are obtained by exchanging the bearer token at the
    configured STS endpoint (AssumeRoleWithWebIdentity).
    """

    def __init__(
        self, config: ConfigValidationModel, auth: AuthValidationModel
    ) -> None:
        """
        Exchange the bearer token for temporary MinIO credentials via STS
        and create an authenticated Minio client.

        Parameters
        ----------
        - config: Validated infrastructure configuration (STS endpoint,
          MinIO endpoint, output bucket).
        - auth: Validated authentication details used to obtain the bearer
          token.
        """
        bearer = resolve_bearer(auth)
        credentials = exchange_minio_token(bearer, config.minio_sts_endpoint)
        secure = is_https(config.minio_endpoint)
        # Minio() only accepts host:port — strip any http(s):// prefix.
        endpoint = strip_scheme(config.minio_endpoint)
        self._client = Minio(
            endpoint,
            access_key=credentials.access_key,
            secret_key=credentials.secret_key,
            session_token=credentials.session_token,
            secure=secure,
        )
        self._config = config
        logger.info(
            "MinIO client initialised (endpoint=%s, secure=%s)",
            config.minio_endpoint,
            secure,
        )

    def download_results(
        self,
        task_id: str,
        output_dir: Path,
        bucket: str | None = None,
    ) -> list[Path]:
        """
        Download all output objects for a task to a local directory.

        Each object is written to ``output_dir/<filename>``, stripping the
        leading ``<task_id>/`` prefix that MinIO uses as a folder separator.

        Parameters
        ----------
        - task_id: ID returned by the TES submission.
        - output_dir: Local directory to write the downloaded files into.
          The directory (and any missing parents) is created automatically.
        - bucket: Override the bucket from config.

        Returns
        -------
        List of :class:`~pathlib.Path` objects pointing to every downloaded
        file.
        """
        object_paths = list_results(self._client, self._config, task_id, bucket=bucket)

        downloaded: list[Path] = []
        for path in object_paths:
            logger.info("Downloading result object: %s", path)
            local_path = download_result(
                self._client, self._config, path, output_dir, bucket=bucket
            )
            downloaded.append(local_path)

        return downloaded
