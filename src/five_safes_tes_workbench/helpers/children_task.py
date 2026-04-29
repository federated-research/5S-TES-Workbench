from dataclasses import dataclass
import requests
from ..schema.config_schema import ConfigValidationModel
from ..utils.logger import get_logger
from ..constants.task_status import TASK_STATUS_DESCRIPTIONS, TaskStatus

logger = get_logger(__name__)


@dataclass
class ChildTaskInfo:
    """
    Information about a child task.

    Attributes:
    -----------
    - id: The ID of the child task.
    - status: The status of the child task.
    """

    id: str
    status: TaskStatus


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
