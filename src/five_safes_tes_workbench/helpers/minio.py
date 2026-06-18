from dataclasses import dataclass
from pathlib import Path

import minio
from minio import Minio

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
