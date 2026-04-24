from minio import Minio
import requests
from ..schema.config_schema import ConfigValidationModel
from urllib.parse import urlparse
from ..utils.logger import get_logger

logger = get_logger(__name__)


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


def get_child_task_id(
    config: ConfigValidationModel, parent_task_id: str, tre: str
) -> str:
    """
    Get the child task ID for a given task and TRE.
    """
    response = requests.get(
        f"{config.tes_base_url.rstrip('/')}/api/Submission/GetChildSubmissionIdByParentAndTre?parentSubmissionId={parent_task_id}&treName={tre}"
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get child task ID: {response.status_code} {response.text}"
        )

    child_task_id = response.json()
    if child_task_id is None:
        raise RuntimeError(
            f"No child task ID found for parent task {parent_task_id} and TRE {tre}"
        )
    logger.info("Child task ID: %s", child_task_id)
    return child_task_id
