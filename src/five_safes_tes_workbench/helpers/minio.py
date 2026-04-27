import csv
import json
from dataclasses import dataclass
from typing import Any
from io import StringIO
from minio import Minio
import minio
import requests
from five_safes_tes_workbench.constants.task_status import (
    TASK_STATUS_DESCRIPTIONS,
    TaskStatus,
)
from ..schema.config_schema import ConfigValidationModel
from urllib.parse import urlparse
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChildTaskInfo:
    id: str
    status: TaskStatus


def require_client(client: Minio | None) -> Minio:
    if client is None:
        raise ValueError(
            "MinIO client is not initialised. "
            "Please call fetch_results() after submit()."
        )
    return client


def require_config(config: ConfigValidationModel | None) -> ConfigValidationModel:
    if config is None:
        raise ValueError(
            "MinIO builder has no config. Please call fetch_results() after submit()."
        )
    return config


def is_https(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return True
    if parsed.scheme == "http":
        return False
    raise ValueError(f"URL must start with http:// or https://, got: {url!r}")


def get_child_task_info(
    config: ConfigValidationModel, parent_task_id: str, tre: str
) -> ChildTaskInfo:
    """
    Get the child task ID for a given task and TRE.
    """
    response = requests.get(
        f"{config.tes_base_url.rstrip('/')}/api/Submission/GetChildSubmissionInfoByParentAndTre?parentSubmissionId={parent_task_id}&treName={tre}"
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get child task ID: {response.status_code} {response.text}"
        )

    child_task_info = response.json()
    if child_task_info is None:
        raise RuntimeError(
            f"No child task ID found for parent task {parent_task_id} and TRE {tre}"
        )
    logger.info(
        "Child task ID: %s, status: %s",
        child_task_info["id"],
        TASK_STATUS_DESCRIPTIONS[TaskStatus(child_task_info["status"])],
    )
    return ChildTaskInfo(
        id=child_task_info["id"],
        status=TaskStatus(child_task_info["status"]),
    )


def check_child_task_status(child_task_info: ChildTaskInfo) -> str | None:
    """
    Check the status of a child task and return an error message if the task is not completed.

    Parameters
    ----------
    - child_task_info: The child task information.

    Returns
    -------
    An error message if the task is not completed, failed or cancelled, otherwise None.
    """
    if (
        child_task_info.status == TaskStatus.FAILED
        or child_task_info.status == TaskStatus.CANCELLED
        or child_task_info.status == TaskStatus.FAILURE
    ):
        return (
            f"Child task {child_task_info.id} is failed or cancelled. Please try again."
        )

    elif child_task_info.status != TaskStatus.COMPLETED:
        return f"Child task {child_task_info.id} is not completed, so results are not available yet. Please wait for the task to complete and try again. Current status: {TASK_STATUS_DESCRIPTIONS[TaskStatus(child_task_info.status)]}"
    return None


def list_results(
    client: Minio | None,
    config: ConfigValidationModel | None,
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

    Returns
    -------
    List of object names found under the task prefix.
    """
    client = require_client(client)
    resolved_bucket = bucket or require_config(config).minio_output_bucket
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
    client: Minio | None,
    config: ConfigValidationModel | None,
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

    Returns
    -------
    String content of the object, or ``None`` if the object does not
    exist.
    """
    client = require_client(client)
    resolved_bucket = bucket or require_config(config).minio_output_bucket

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
