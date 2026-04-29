"""Builder responsible for fetching task results from MinIO after submission."""

from typing import Any
from minio import Minio
from ..helpers.minio import list_results, get_and_parse_result, exchange_minio_token
from ..helpers.auth import resolve_bearer
from ..helpers.url import is_https
from ..schema.config_schema import ConfigValidationModel
from ..schema.auth_schema import AuthValidationModel
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
        # Check if the MinIO endpoint is HTTPS
        secure = is_https(config.minio_endpoint)
        self._client = Minio(
            config.minio_endpoint,
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

    def fetch_result(
        self, task_id: str, bucket: str | None = None
    ) -> dict[str, str | dict[str, Any] | list[Any] | None]:
        """
        Fetch all output objects for a task and return them as a mapping
        of ``object_path -> parsed_content``.

        Uses :meth:`get_result_parsed` for each object so content is
        automatically decoded from JSON / CSV where possible.

        Parameters
        ----------
        - task_id: ID returned by the TES submission.
        - bucket: Override the bucket from config.

        Returns
        -------
        Dict mapping each object path to its parsed content.
        """
        object_paths = list_results(self._client, self._config, task_id, bucket=bucket)

        results: dict[str, str | dict[str, Any] | list[Any] | None] = {}
        for path in object_paths:
            logger.info("Fetching result object: %s", path)
            results[path] = get_and_parse_result(
                self._client, self._config, path, bucket=bucket
            )

        return results
