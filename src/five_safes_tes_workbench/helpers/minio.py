from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

from ..utils.logger import get_logger

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

logger = get_logger(__name__)


@dataclass
class MinioCredentials:
    """
    Temporary S3 credentials returned by the STS token exchange.

    Attributes:
    -----------
    - access_key: Access key for the S3 client.
    - secret_key: Secret key for the S3 client.
    - session_token: Session token for the S3 client.
    """

    access_key: str
    secret_key: str
    session_token: str


def list_results(
    client: "S3Client",
    task_id: str,
    bucket: str,
) -> list[str]:
    """
    List all output objects written by a task.

    Objects are expected to live under the ``{task_id}/`` prefix in the
    configured output bucket.

    Parameters
    ----------
    - task_id: ID returned by the TES submission.
    - client: boto3 S3 client (should be already initialized before calling this function).
    - bucket: Output bucket for the project.

    Returns
    -------
    List of object names found under the task prefix.
    """

    prefix = f"{task_id}/"

    try:
        paginator = client.get_paginator("list_objects_v2")
        names = [
            obj["Key"]
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
            if obj.get("Key")
        ]
        if not names:
            logger.warning("No result objects found for task %s", task_id)
            return []
        logger.info("Found %d result object(s) for task %s", len(names), task_id)
        return names
    except Exception as e:
        logger.error("Error listing results for task %s: %s", task_id, e)
        raise


def download_result(
    client: "S3Client",
    object_path: str,
    output_dir: Path,
    bucket: str,
) -> Path:
    """
    Download a single result object from S3 to a local file.

    The ``<task_id>/`` prefix is stripped from ``object_path`` so that
    only the filename (and any sub-path) is preserved under ``output_dir``.

    Parameters
    ----------
    - client: Authenticated boto3 S3 client.
    - bucket: Output bucket for the project.
    - object_path: Full object path within the bucket (e.g.
        ``"<task_id>/output.csv"``).
    - output_dir: Local directory to write the file into.

    Returns
    -------
    The :class:`~pathlib.Path` of the downloaded local file.
    """

    # Strip the leading <task_id>/ prefix so the filename is clean.
    parts = object_path.split("/", 1)
    relative_name = parts[1] if len(parts) > 1 else object_path

    local_path = output_dir / relative_name
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client.download_file(bucket, object_path, str(local_path))
        logger.info("Downloaded %s -> %s", object_path, local_path)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in {"NoSuchKey", "404"}:
            logger.warning("Object not found, skipping: %s", object_path)
        raise

    return local_path
