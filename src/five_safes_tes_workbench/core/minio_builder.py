"""Builder responsible for fetching task results from MinIO after submission."""

import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Any
from urllib.parse import urlparse

import requests
from minio import Minio
import minio

from ..schema.config_schema import ConfigValidationModel
from ..schema.auth_schema import AuthValidationModel
from ..core.submit_builder import WorkbenchSubmitBuilder
from ..utils.logger import get_logger

logger = get_logger(__name__)

_STS_NS = {"sts": "https://sts.amazonaws.com/doc/2011-06-15/"}
_STS_DURATION_SECONDS = "3600"


class WorkbenchMinioBuilder:
    """
    Builder responsible for connecting to MinIO and retrieving task
    output objects after a TES task has completed.

    Credentials are obtained by exchanging the bearer token at the
    configured STS endpoint (AssumeRoleWithWebIdentity).
    """

    def __init__(self) -> None:
        self._client: Minio | None = None
        self._config: ConfigValidationModel | None = None

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialise(
        self,
        config: ConfigValidationModel,
        auth: AuthValidationModel,
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
        bearer = WorkbenchSubmitBuilder._resolve_bearer(auth)
        credentials = self._exchange_token(bearer, config.minio_sts_endpoint)

        secure = _is_https(config.minio_sts_endpoint)

        self._client = Minio(
            config.minio_endpoint,
            access_key=credentials["access_key"],
            secret_key=credentials["secret_key"],
            session_token=credentials["session_token"],
            secure=secure,
        )
        self._config = config

        logger.info("MinIO client initialised (endpoint=%s, secure=%s)", config.minio_endpoint, secure)

    # ------------------------------------------------------------------
    # Public result-fetching methods
    # ------------------------------------------------------------------

    def list_results(self, task_id: str, bucket: str | None = None) -> list[str]:
        """
        List all output objects written by a task.

        Objects are expected to live under the ``{task_id}/`` prefix in the
        configured output bucket.

        Parameters
        ----------
        - task_id: ID returned by the TES submission.
        - bucket: Override the bucket from config. Defaults to
          ``config.minio_output_bucket``.

        Returns
        -------
        List of object names found under the task prefix.
        """
        client = self._require_client()
        resolved_bucket = bucket or self._require_config().minio_output_bucket
        prefix = f"{task_id}/"

        try:
            objects = client.list_objects(resolved_bucket, prefix=prefix, recursive=True)
            names = [obj.object_name for obj in objects]
            logger.info("Found %d result object(s) for task %s", len(names), task_id)
            return names
        except Exception as e:
            logger.error("Error listing results for task %s: %s", task_id, e)
            raise

    def get_result(self, object_path: str, bucket: str | None = None) -> str | None:
        """
        Fetch a single result object as a raw UTF-8 string.

        Parameters
        ----------
        - object_path: Full object path within the bucket (e.g.
          ``"<task_id>/stdout"``)
        - bucket: Override the bucket from config.

        Returns
        -------
        String content of the object, or ``None`` if the object does not
        exist.
        """
        client = self._require_client()
        resolved_bucket = bucket or self._require_config().minio_output_bucket

        try:
            response = client.get_object(resolved_bucket, object_path)
            content = response.read().decode("utf-8")
            response.close()
            response.release_conn()
            return content
        except minio.error.S3Error as e:
            if e.code == "NoSuchKey":
                logger.warning("Object not found: %s", object_path)
                return None
            raise

    def get_result_parsed(
        self, object_path: str, bucket: str | None = None
    ) -> str | dict[str, Any] | list[Any] | None:
        """
        Fetch a single result object and auto-detect its format.

        Attempts JSON first, then CSV (returning the first row as a dict),
        then falls back to a raw string.

        Parameters
        ----------
        - object_path: Full object path within the bucket.
        - bucket: Override the bucket from config.
        """
        content = self.get_result(object_path, bucket=bucket)
        if content is None:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        try:
            reader = csv.DictReader(StringIO(content))
            rows = list(reader)
            if rows:
                return rows
        except Exception:
            pass

        return content

    def fetch_all_results(
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
        object_paths = self.list_results(task_id, bucket=bucket)

        results: dict[str, str | dict[str, Any] | list[Any] | None] = {}
        for path in object_paths:
            logger.info("Fetching result object: %s", path)
            results[path] = self.get_result_parsed(path, bucket=bucket)

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_client(self) -> Minio:
        if self._client is None:
            raise ValueError(
                "MinIO client is not initialised. "
                "Please call fetch_results() after submit()."
            )
        return self._client

    def _require_config(self) -> ConfigValidationModel:
        if self._config is None:
            raise ValueError(
                "MinIO builder has no config. "
                "Please call fetch_results() after submit()."
            )
        return self._config

    @staticmethod
    def _exchange_token(bearer: str, sts_endpoint: str) -> dict[str, str]:
        """
        Call the STS AssumeRoleWithWebIdentity action and return temporary
        AWS-style credentials.
        """
        logger.info("Exchanging bearer token for MinIO credentials via STS (%s)", sts_endpoint)

        response = requests.post(
            sts_endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "Action": "AssumeRoleWithWebIdentity",
                "Version": "2011-06-15",
                "DurationSeconds": _STS_DURATION_SECONDS,
                "WebIdentityToken": bearer,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"STS token exchange failed ({response.status_code}): {response.text}"
            )

        root = ET.fromstring(response.text)
        credentials = root.find(".//sts:Credentials", _STS_NS)

        if credentials is None:
            raise RuntimeError("STS response contained no Credentials element")

        return {
            "access_key": credentials.findtext("sts:AccessKeyId", namespaces=_STS_NS) or "",
            "secret_key": credentials.findtext("sts:SecretAccessKey", namespaces=_STS_NS) or "",
            "session_token": credentials.findtext("sts:SessionToken", namespaces=_STS_NS) or "",
        }


# ------------------------------------------------------------------
# Module-level helper
# ------------------------------------------------------------------

def _is_https(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return True
    if parsed.scheme == "http":
        return False
    raise ValueError(f"URL must start with http:// or https://, got: {url!r}")
