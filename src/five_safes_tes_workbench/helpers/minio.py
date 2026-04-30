from dataclasses import dataclass
from pathlib import Path
from minio import Minio
import minio
import requests
import xml.etree.ElementTree as ET

from ..constants.minio import (
    STS_DURATION_SECONDS,
    STS_NAMESPACE,
    STS_TOKEN_EXCHANGE_TIMEOUT,
)
from ..schema.config_schema import ConfigValidationModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MinioCredentials:
    """
    MinIO credentials type.

    Attributes:
    -----------
    - access_key: The access key for the MinIO client.
    - secret_key: The secret key for the MinIO client.
    - session_token: The session token for the MinIO client.
    """

    access_key: str
    secret_key: str
    session_token: str


def list_results(
    client: Minio,
    config: ConfigValidationModel,
    task_id: str,
    bucket: str | None = None,
) -> list[str]:
    """
    List all output objects written by a task.

    Objects are expected to live under the ``{task_id}/`` prefix in the
    configured output bucket.

    Parameters
    ----------
    - task_id: ID returned by the TES submission.
    - bucket: Override the bucket from config. Defaults to
        ``config.minio_output_bucket``.
    - client: MinIO client (should be already initialised before calling this function).
    - config: ConfigValidationModel (should be already validated before calling this function).

    Returns
    -------
    List of object names found under the task prefix.
    """

    resolved_bucket = bucket or config.minio_output_bucket
    prefix = f"{task_id}/"

    try:
        objects = client.list_objects(resolved_bucket, prefix=prefix, recursive=True)
        names = [obj.object_name for obj in objects]
        logger.info("Found %d result object(s) for task %s", len(names), task_id)
        return names
    except Exception as e:
        logger.error("Error listing results for task %s: %s", task_id, e)
        raise


def download_result(
    client: Minio,
    config: ConfigValidationModel,
    object_path: str,
    output_dir: Path,
    bucket: str | None = None,
) -> Path:
    """
    Download a single result object from MinIO to a local file.

    The ``<task_id>/`` prefix is stripped from ``object_path`` so that
    only the filename (and any sub-path) is preserved under ``output_dir``.

    Parameters
    ----------
    - client: Authenticated MinIO client.
    - config: Validated infrastructure configuration.
    - object_path: Full object path within the bucket (e.g.
        ``"<task_id>/output.csv"``).
    - output_dir: Local directory to write the file into.
    - bucket: Override the bucket from config.

    Returns
    -------
    The :class:`~pathlib.Path` of the downloaded local file.
    """
    resolved_bucket = bucket or config.minio_output_bucket

    # Strip the leading <task_id>/ prefix so the filename is clean.
    parts = object_path.split("/", 1)
    relative_name = parts[1] if len(parts) > 1 else object_path

    local_path = output_dir / relative_name
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client.fget_object(resolved_bucket, object_path, str(local_path))
        logger.info("Downloaded %s -> %s", object_path, local_path)
    except minio.error.S3Error as e:
        if e.code == "NoSuchKey":
            logger.warning("Object not found, skipping: %s", object_path)
            raise
        raise

    return local_path


def _parse_sts_response(response: requests.Response) -> MinioCredentials:
    """
    Parse and validate the STS response and return the credentials.

    Parameters
    ----------
    - response: The response from the STS endpoint.

    Returns
    -------
    A MinioCredentials object.
    """
    root = ET.fromstring(response.text)
    credentials = root.find(".//sts:Credentials", STS_NAMESPACE)

    if credentials is None:
        raise RuntimeError("STS response contained no Credentials element")

    access_key = credentials.findtext("sts:AccessKeyId", namespaces=STS_NAMESPACE)
    secret_key = credentials.findtext("sts:SecretAccessKey", namespaces=STS_NAMESPACE)
    session_token = credentials.findtext("sts:SessionToken", namespaces=STS_NAMESPACE)

    if access_key is None or secret_key is None or session_token is None:
        raise RuntimeError("STS response did not contain all required credentials")

    return MinioCredentials(
        access_key=access_key, secret_key=secret_key, session_token=session_token
    )


def exchange_minio_token(bearer: str, sts_endpoint: str) -> MinioCredentials:
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

    return _parse_sts_response(response)
