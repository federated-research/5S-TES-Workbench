import csv
import json
from typing import Any
from io import StringIO
from minio import Minio
import minio
from ..schema.config_schema import ConfigValidationModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


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


def get_and_parse_result(
    client: Minio,
    config: ConfigValidationModel,
    object_path: str,
    bucket: str | None = None,
) -> str | dict[str, Any] | list[Any] | None:
    """
    Fetch a single result object and auto-detect its format.

    Attempts JSON first, then CSV (returning the first row as a dict),
    then falls back to a raw string.

    Parameters
    ----------
    - object_path: Full object path within the bucket (e.g.
        ``"<task_id>/stdout"``)
    - bucket: Override the bucket from config.
    - client: MinIO client (should be already initialised before calling this function).
    - config: ConfigValidationModel (should be already validated before calling this function).

    Returns
    -------
    String content of the object, or ``None`` if the object does not
    exist.
    """

    resolved_bucket = bucket or config.minio_output_bucket

    try:
        response = client.get_object(resolved_bucket, object_path)
        content = response.read().decode("utf-8")
        response.close()
        response.release_conn()

        if content is None:
            logger.warning("Object not found: %s", object_path)
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

    except minio.error.S3Error as e:
        if e.code == "NoSuchKey":
            logger.warning("Object not found: %s", object_path)
            return None
        raise
