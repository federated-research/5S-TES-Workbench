import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import minio
import requests
from minio import Minio

from ..constants.minio import (
    STS_DURATION_SECONDS,
    STS_NAMESPACE,
    STS_TOKEN_EXCHANGE_TIMEOUT,
)
from ..schema.config_schema import ConfigValidationModel
from ..utils.logger import get_logger

logger = get_logger(__name__)

STS_ACTION = "AssumeRoleWithWebIdentity"
STS_VERSION = "2011-06-15"


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
) -> list[str]:
    """
    List all output objects written by a task.

    Objects are expected to live under the ``{task_id}/`` prefix in the
    configured output bucket.

    Parameters
    ----------
    - task_id: ID returned by the TES submission.
    - client: MinIO client (should be already initialized before calling this function).
    - config: ConfigValidationModel (should be already validated before calling this function).

    Returns
    -------
    List of object names found under the task prefix.
    """

    resolved_bucket = config.minio_output_bucket
    prefix = f"{task_id}/"

    try:
        objects = client.list_objects(resolved_bucket, prefix=prefix, recursive=True)
        names = [obj.object_name for obj in objects if obj.object_name is not None]
        if not names:
            logger.warning("No result objects found for task %s", task_id)
            return []
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

    Returns
    -------
    The :class:`~pathlib.Path` of the downloaded local file.
    """
    resolved_bucket = config.minio_output_bucket

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
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as exc:
        raise RuntimeError(
            f"STS response is not valid XML (status {response.status_code}). "
            f"Raw response:\n{response.text!r}"
        ) from exc

    credentials = root.find(".//sts:Credentials", STS_NAMESPACE)
    if credentials is None:
        credentials = next(
            (element for element in root.iter() if _local_name(element.tag) == "Credentials"),
            None,
        )

    if credentials is None:
        raise RuntimeError("STS response contained no Credentials element")

    access_key = _find_child_text(credentials, "AccessKeyId")
    secret_key = _find_child_text(credentials, "SecretAccessKey")
    session_token = _find_child_text(credentials, "SessionToken")

    if access_key is None or secret_key is None or session_token is None:
        raise RuntimeError("STS response did not contain all required credentials")

    return MinioCredentials(
        access_key=access_key, secret_key=secret_key, session_token=session_token
    )


def _local_name(tag: str) -> str:
    """Return an XML tag name without its optional namespace."""
    return tag.rsplit("}", 1)[-1]


def _find_child_text(element: ET.Element, child_name: str) -> str | None:
    child = next(
        (child for child in element if _local_name(child.tag) == child_name),
        None,
    )
    return child.text if child is not None else None


def _sts_endpoint_candidates(sts_endpoint: str) -> list[str]:
    """
    Return STS endpoints to try.

    MinIO commonly exposes STS at ``/sts``. RustFS routes
    ``AssumeRoleWithWebIdentity`` at the service root.
    """
    parsed = urlsplit(sts_endpoint)
    candidates = [sts_endpoint]
    if parsed.path.rstrip("/") == "/sts":
        root_endpoint = urlunsplit(
            (parsed.scheme, parsed.netloc, "", parsed.query, parsed.fragment)
        )
        candidates.append(root_endpoint)
    return candidates


def _should_try_next_sts_endpoint(response: requests.Response) -> bool:
    return (
        response.status_code == 501
        and "NotImplemented" in response.text
        and "Unknown operation" in response.text
    )


def exchange_minio_token(bearer: str, sts_endpoint: str) -> MinioCredentials:
    """
    Call the STS AssumeRoleWithWebIdentity action and return temporary
    AWS-style credentials.
    """
    logger.info(
        "Exchanging bearer token for MinIO credentials via STS (%s)", sts_endpoint
    )

    response = None
    candidates = _sts_endpoint_candidates(sts_endpoint)

    for endpoint in candidates:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "Action": STS_ACTION,
                "Version": STS_VERSION,
                "DurationSeconds": STS_DURATION_SECONDS,
                "WebIdentityToken": bearer,
            },
            timeout=STS_TOKEN_EXCHANGE_TIMEOUT,
        )

        if response.status_code == 200:
            return _parse_sts_response(response)

        if endpoint != candidates[-1] and _should_try_next_sts_endpoint(response):
            logger.warning(
                "STS endpoint %s did not recognize %s; retrying service root",
                endpoint,
                STS_ACTION,
            )
            continue

        raise RuntimeError(
            f"STS token exchange failed ({response.status_code}): {response.text}"
        )

    if response is None:
        raise RuntimeError("STS token exchange failed: no endpoint candidates")

    return _parse_sts_response(response)
