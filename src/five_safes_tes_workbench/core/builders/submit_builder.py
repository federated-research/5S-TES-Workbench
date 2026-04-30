import requests

from ..helpers.auth import fetch_keycloak_token, resolve_bearer
from ..utils.logger import get_logger

from ..schema.config_schema import ConfigValidationModel
from ..schema.auth_schema import AuthValidationModel
from ..common.validator_enums import AuthMode

import tes  # type: ignore

from ...common.enums.validator_enums import AuthMode
from ...common.exceptions.submission_errors import SubmissionError
from ...schema.auth_schema import AuthValidationModel
from ...schema.config_schema import ConfigValidationModel
from ...utils.logger import get_logger

logger = get_logger(__name__)


class WorkbenchSubmit():
    """
    Class responsible for submitting TES tasks
    to the Submission API.

    It takes the validated configuration, constructed test
    task and setup the necessary authentication to
    submit the task to the TES endpoint.
    """

    def submit(
        self,
        config: ConfigValidationModel,
        auth: AuthValidationModel,
        task: tes.Task,
    ) -> str:
        """
        Submits the given TES task to the configured TES endpoint.

        Attributes:
             - `config`: Validated configuration containing TES endpoint
               and other settings.

             - `auth`: Validated authentication details for accessing
               the TES endpoint.

             - `task`: The TES task to be submitted.

        Returns:
             - The ID of the submitted task.

        """

        try:

        base_url = config.tes_base_url.rstrip("/")
        endpoint = f"{base_url}/v1/tasks"
        bearer = resolve_bearer(auth)

            base_url = config.tes_base_url.rstrip("/")
            endpoint = f"{base_url}/v1/tasks"
            bearer = self._resolve_bearer(auth)

            logger.info("Submitting task to %s/v1/tasks", base_url)

        if response.status_code == 401 and auth.auth_mode == AuthMode.CREDENTIALS:
            logger.info("Received 401, retrying with fresh keycloak token...")
            bearer = fetch_keycloak_token(auth)
            response = self._post_task(endpoint, _task_json, bearer)

            if response.status_code == 401 and auth.auth_mode == AuthMode.CREDENTIALS:
                logger.info("Received 401, retrying with fresh keycloak token...")
                bearer = self._fetch_keycloak_token(auth)
                response = self._post_task(endpoint, _task_json, bearer)

            response.raise_for_status()
            task_id = response.json()["id"]

            logger.info("Task submitted successfully! ID: %s", task_id)
            return task_id

        except Exception as e:
            raise SubmissionError(
                f"Unexpected error during submission: {e}"
            ) from e

    @staticmethod
    def _post_task(
        endpoint: str,
        task_json: str,
        bearer: str,
    ) -> requests.Response:
        """
        Helper method to post the task to the TES endpoint.

        Attributes:
             - `endpoint`: The full URL of the TES endpoint to submit to.
             - `task_json`: The TES task serialized as a JSON string.
             - `bearer`: The bearer token for authentication.

        Returns:
             - The HTTP response from the TES endpoint.
        """
        return requests.post(
            endpoint,
            data=task_json,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer}",
            },
            timeout=60,
        )
