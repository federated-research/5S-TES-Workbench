from typing import Protocol

import tes  # type: ignore

from ...schema.auth_schema import AuthValidationModel
from ...schema.config_schema import ConfigValidationModel


class SubmissionProtocol(Protocol):
    """
    Protocol for submitting TES tasks.

    Any class that implements this protocol must provide:
        - `submit()`: Submits a task and returns the task ID.
    """

    def submit(
        self,
        config: ConfigValidationModel,
        auth: AuthValidationModel,
        task: tes.Task,
    ) -> str: ...