import requests
import tes  # type: ignore

from ...common.enums.validator_enums import AuthMode
from ...common.exceptions.submission_errors import CancellationError, SubmissionError
from ...helpers.auth import fetch_keycloak_access_token, resolve_bearer
from ...schema.auth_schema import AuthValidationModel
from ...schema.config_schema import ConfigValidationModel
from ...utils.logger import get_logger

logger = get_logger(__name__)


class WorkbenchSubmit:
    """
    Class responsible for submitting and cancelling TES tasks
    via the Submission API.

    It takes the validated configuration, constructed TES
    task and setup the necessary authentication to
    submit or cancel a task at the TES endpoint.
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
            _task_json: str = task.as_json()

            response = self._post_task(endpoint, _task_json, bearer)

            if response.status_code == 401 and auth.auth_mode == AuthMode.CREDENTIALS:
                logger.info("Received 401, retrying with fresh keycloak access token...")
                bearer = fetch_keycloak_access_token(auth)
                response = self._post_task(endpoint, _task_json, bearer)

            response.raise_for_status()
            task_id = response.json()["id"]

            logger.info("Task submitted successfully! ID: %s", task_id)
            return task_id

        except Exception as e:
            raise SubmissionError(f"Unexpected error during submission: {e}") from e

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

    def cancel(
        self,
        config: ConfigValidationModel,
        auth: AuthValidationModel,
        task_id: str,
    ) -> str:
        """
        Cancels a TES task at the configured TES endpoint.

        Attributes:
             - `config`: Validated configuration containing TES endpoint
               and other settings.

             - `auth`: Validated authentication details for accessing
               the TES endpoint.

             - `task_id`: The ID of the TES task to cancel.

        Returns:
             - The ID of the cancelled task.
        """

        try:
            base_url = config.tes_base_url.rstrip("/")
            endpoint = f"{base_url}/v1/tasks/{task_id}:cancel"
            bearer = resolve_bearer(auth)

            response = self._cancel_task(endpoint, bearer)

            if response.status_code == 401 and auth.auth_mode == AuthMode.CREDENTIALS:
                logger.info("Received 401, retrying with fresh keycloak access token...")
                bearer = fetch_keycloak_access_token(auth)
                response = self._cancel_task(endpoint, bearer)

            response.raise_for_status()

            logger.info("Task cancelled successfully! ID: %s", task_id)
            return task_id

        except Exception as e:
            raise CancellationError(f"Unexpected error during cancellation: {e}") from e

    @staticmethod
    def _cancel_task(
        endpoint: str,
        bearer: str,
    ) -> requests.Response:
        """
        Helper method to POST a cancel request to the TES endpoint.

        Attributes:
             - `endpoint`: The full URL of the TES cancel endpoint.
             - `bearer`: The bearer token for authentication.

        Returns:
             - The HTTP response from the TES endpoint.
        """
        return requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {bearer}",
            },
            timeout=60,
        )
