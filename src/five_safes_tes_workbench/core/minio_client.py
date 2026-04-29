"""Builder responsible for fetching task results from MinIO after submission."""

from typing import Any
import requests
from minio import Minio
import xml.etree.ElementTree as ET

from ..constants.minio import (
    STS_DURATION_SECONDS,
    STS_NAMESPACE,
    STS_TOKEN_EXCHANGE_TIMEOUT,
)

from ..helpers.minio import list_results, get_and_parse_result
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
        credentials = self._exchange_token(bearer, config.minio_sts_endpoint)

        secure = is_https(config.minio_sts_endpoint)
        self._client = Minio(
            config.minio_endpoint,
            access_key=credentials["access_key"],
            secret_key=credentials["secret_key"],
            session_token=credentials["session_token"],
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

    @staticmethod
    def _exchange_token(bearer: str, sts_endpoint: str) -> dict[str, str]:
        """
        Call the STS AssumeRoleWithWebIdentity action and return temporary
        AWS-style credentials.
        """
        logger.info(
            "Exchanging bearer token for MinIO credentials via STS (%s)", sts_endpoint
        )

        response = requests.post(
            sts_endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "Action": "AssumeRoleWithWebIdentity",
                "Version": "2011-06-15",
                "DurationSeconds": STS_DURATION_SECONDS,
                "WebIdentityToken": bearer,
            },
            timeout=STS_TOKEN_EXCHANGE_TIMEOUT,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"STS token exchange failed ({response.status_code}): {response.text}"
            )

        root = ET.fromstring(response.text)
        credentials = root.find(".//sts:Credentials", STS_NAMESPACE)

        if credentials is None:
            raise RuntimeError("STS response contained no Credentials element")

        return {
            "access_key": credentials.findtext(
                "sts:AccessKeyId", namespaces=STS_NAMESPACE
            )
            or "",
            "secret_key": credentials.findtext(
                "sts:SecretAccessKey", namespaces=STS_NAMESPACE
            )
            or "",
            "session_token": credentials.findtext(
                "sts:SessionToken", namespaces=STS_NAMESPACE
            )
            or "",
        }
