import tes  # type: ignore
import json
import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List, TypedDict, Union
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse
from enum import IntEnum

from five_safes_tes_workbench.auth.submission_api_session import SubmissionAPISession


# Load environment variables from .env file
load_dotenv()


class TaskStatus(IntEnum):
    """
    Enum for task status codes with their corresponding display names.
    source: https://github.com/SwanseaUniversityMedical/DARE-Control/blob/main/src/BL/Models/Enums/Enums.cs
    """

    # Parent only
    WAITING_FOR_CHILD_SUBS_TO_COMPLETE = 0
    # Stage 1
    WAITING_FOR_AGENT_TO_TRANSFER = 1
    # Stage 2
    TRANSFERRED_TO_POD = 2
    # Stage 3
    POD_PROCESSING = 3
    # Stage 3 - Green
    POD_PROCESSING_COMPLETE = 4
    # Stage 4
    DATA_OUT_APPROVAL_BEGUN = 5
    # Stage 4 - Red
    DATA_OUT_APPROVAL_REJECTED = 6
    # Stage 4 - Green
    DATA_OUT_APPROVED = 7
    # Stage 1 - Red
    USER_NOT_ON_PROJECT = 8
    # Stage 2 - Red
    INVALID_USER = 9
    # Stage 2 - Red
    TRE_NOT_AUTHORISED_FOR_PROJECT = 10
    # Stage 5 - Green (completed enum)
    COMPLETED = 11
    # Stage 1 - Red
    INVALID_SUBMISSION = 12
    # Stage 1 - Red
    CANCELLING_CHILDREN = 13
    # Stage 1 - Red
    REQUEST_CANCELLATION = 14
    # Stage 1 - Red
    CANCELLATION_REQUEST_SENT = 15
    # Stage 5 - Red
    CANCELLED = 16
    # Stage 1
    SUBMISSION_WAITING_FOR_CRATE_FORMAT_CHECK = 17
    # Unused
    VALIDATING_USER = 18
    # Unused
    VALIDATING_SUBMISSION = 19
    # Unused - Green
    VALIDATION_SUCCESSFUL = 20
    # Stage 2
    AGENT_TRANSFERRING_TO_POD = 21
    # Stage 2 - Red
    TRANSFER_TO_POD_FAILED = 22
    # Unused
    TRE_REJECTED_PROJECT = 23
    # Unused
    TRE_APPROVED_PROJECT = 24
    # Stage 3 - Red
    POD_PROCESSING_FAILED = 25
    # Stage 1 - Parent only
    RUNNING = 26
    # Stage 5 - Red
    FAILED = 27
    # Stage 2
    SENDING_SUBMISSION_TO_HUTCH = 28
    # Stage 4
    REQUESTING_HUTCH_DOES_FINAL_PACKAGING = 29
    # Stage 3
    WAITING_FOR_CRATE = 30
    # Stage 3
    FETCHING_CRATE = 31
    # Stage 3
    QUEUED = 32
    # Stage 3
    VALIDATING_CRATE = 33
    # Stage 3
    FETCHING_WORKFLOW = 34
    # Stage 3
    STAGING_WORKFLOW = 35
    # Stage 3
    EXECUTING_WORKFLOW = 36
    # Stage 3
    PREPARING_OUTPUTS = 37
    # Stage 3
    DATA_OUT_REQUESTED = 38
    # Stage 3
    TRANSFERRED_FOR_DATA_OUT = 39
    # Stage 3
    PACKAGING_APPROVED_RESULTS = 40
    # Stage 3 - Green
    COMPLETE = 41
    # Stage 3 - Red
    FAILURE = 42
    # Stage 1
    SUBMISSION_RECEIVED = 43
    # Stage 1 - Green
    SUBMISSION_CRATE_VALIDATED = 44
    # Stage 1 - Red
    SUBMISSION_CRATE_VALIDATION_FAILED = 45
    # Stage 2 - Green
    TRE_CRATE_VALIDATED = 46
    # Stage 2 - Red
    TRE_CRATE_VALIDATION_FAILED = 47
    # Stage 2
    TRE_WAITING_FOR_CRATE_FORMAT_CHECK = 48
    # Stage 5 - Green - Parent Only
    PARTIAL_RESULT = 49


# Status lookup dictionary for easy access to display names
TASK_STATUS_DESCRIPTIONS = {
    TaskStatus.WAITING_FOR_CHILD_SUBS_TO_COMPLETE: "Waiting for Child Submissions To Complete",
    TaskStatus.WAITING_FOR_AGENT_TO_TRANSFER: "Waiting for Agent To Transfer",
    TaskStatus.TRANSFERRED_TO_POD: "Transferred To Pod",
    TaskStatus.POD_PROCESSING: "Pod Processing",
    TaskStatus.POD_PROCESSING_COMPLETE: "Pod Processing Complete",
    TaskStatus.DATA_OUT_APPROVAL_BEGUN: "Data Out Approval Begun",
    TaskStatus.DATA_OUT_APPROVAL_REJECTED: "Data Out Rejected",
    TaskStatus.DATA_OUT_APPROVED: "Data Out Approved",
    TaskStatus.USER_NOT_ON_PROJECT: "User Not On Project",
    TaskStatus.INVALID_USER: "User not authorised for project on TRE",
    TaskStatus.TRE_NOT_AUTHORISED_FOR_PROJECT: "TRE Not Authorised For Project",
    TaskStatus.COMPLETED: "Completed",
    TaskStatus.INVALID_SUBMISSION: "Invalid Submission",
    TaskStatus.CANCELLING_CHILDREN: "Cancelling Children",
    TaskStatus.REQUEST_CANCELLATION: "Request Cancellation",
    TaskStatus.CANCELLATION_REQUEST_SENT: "Cancellation Request Sent",
    TaskStatus.CANCELLED: "Cancelled",
    TaskStatus.SUBMISSION_WAITING_FOR_CRATE_FORMAT_CHECK: "Waiting For Crate Format Check",
    TaskStatus.VALIDATING_USER: "Validating User",
    TaskStatus.VALIDATING_SUBMISSION: "Validating Submission",
    TaskStatus.VALIDATION_SUCCESSFUL: "Validation Successful",
    TaskStatus.AGENT_TRANSFERRING_TO_POD: "Agent Transferring To Pod",
    TaskStatus.TRANSFER_TO_POD_FAILED: "Transfer To Pod Failed",
    TaskStatus.TRE_REJECTED_PROJECT: "Tre Rejected Project",
    TaskStatus.TRE_APPROVED_PROJECT: "Tre Approved Project",
    TaskStatus.POD_PROCESSING_FAILED: "Pod Processing Failed",
    TaskStatus.RUNNING: "Running",
    TaskStatus.FAILED: "Failed",
    TaskStatus.SENDING_SUBMISSION_TO_HUTCH: "Sending submission to Hutch",
    TaskStatus.REQUESTING_HUTCH_DOES_FINAL_PACKAGING: "Requesting Hutch packages up final output",
    TaskStatus.WAITING_FOR_CRATE: "Waiting for a Crate",
    TaskStatus.FETCHING_CRATE: "Fetching Crate",
    TaskStatus.QUEUED: "Crate queued",
    TaskStatus.VALIDATING_CRATE: "Validating Crate",
    TaskStatus.FETCHING_WORKFLOW: "Fetching workflow",
    TaskStatus.STAGING_WORKFLOW: "Preparing workflow",
    TaskStatus.EXECUTING_WORKFLOW: "Executing workflow",
    TaskStatus.PREPARING_OUTPUTS: "Preparing outputs",
    TaskStatus.DATA_OUT_REQUESTED: "Requested Egress",
    TaskStatus.TRANSFERRED_FOR_DATA_OUT: "Waiting for Egress results",
    TaskStatus.PACKAGING_APPROVED_RESULTS: "Finalising approved results",
    TaskStatus.COMPLETE: "Completed",
    TaskStatus.FAILURE: "Failed",
    TaskStatus.SUBMISSION_RECEIVED: "Submission has been received",
    TaskStatus.SUBMISSION_CRATE_VALIDATED: "Crate Validated",
    TaskStatus.SUBMISSION_CRATE_VALIDATION_FAILED: "Crate Failed Validation",
    TaskStatus.TRE_CRATE_VALIDATED: "Crate Validated",
    TaskStatus.TRE_CRATE_VALIDATION_FAILED: "Crate Failed Validation",
    TaskStatus.TRE_WAITING_FOR_CRATE_FORMAT_CHECK: "Waiting For Crate Format Check",
    TaskStatus.PARTIAL_RESULT: "Complete but not all TREs returned a result",
}


def get_status_description(status_code: int) -> str:
    """
    Get the display description for a given status code.

    Args:
        status_code (int): The numeric status code

    Returns:
        str: The display description for the status code, or "Unknown Status" if not found
    """
    try:
        return TASK_STATUS_DESCRIPTIONS[TaskStatus(status_code)]
    except (ValueError, KeyError):
        return f"Unknown Status ({status_code})"


def get_status_code(description: str) -> int:
    """
    Get the status code for a given display description.

    Args:
        description (str): The display description

    Returns:
        int: The status code, or -1 if not found
    """
    for code, desc in TASK_STATUS_DESCRIPTIONS.items():
        if desc.lower() == description.lower():
            return code.value
    return -1


### there's already executor, input and output classes in tes.py


# @attrs
class Tags(TypedDict):
    """Type definition for tags dictionary, requiring 'Project' and 'tres' keys.
    Note: tres is stored as a pipe-separated string for py-tes compatibility."""

    Project: str
    tres: list[str]

    def to_string(self) -> str:
        """
        Convert the tags dictionary to a pipe-separated string.
        """
        return "|".join([f"{key}:{value}" for key, value in self.items()])


class BaseTESClient(ABC):
    """
    Handles TES (Task Execution Service) operations including task generation and submission.
    """

    def __init__(
        self,
        base_url: str = None,
        TES_url: str = None,
        submission_url: str = None,
        default_image: str = None,
        default_db_config: Dict[str, str] = None,
        default_db_port: str = None,
    ):
        """
        Initialize the TES client. These parameters are typically set in the environment variables, and typically represent properties of the submission, not the task.

        Args:
            base_url (str): Base URL for the TES API
            default_image (str): Default Docker image to use
            default_db_config (Dict[str, str]): Default database configuration
            default_db_port (str): Default database port
        """
        # Use environment variables - required
        self.base_url = base_url or os.getenv("TES_BASE_URL")
        if not self.base_url:
            raise ValueError("TES_BASE_URL environment variable is required")

        # Use pathlib to properly construct URLs
        if TES_url is None:
            parsed = urlparse(self.base_url)
            path = Path(parsed.path) / "v1"
            # Ensure leading slash for URL path
            path_str = str(path) if str(path).startswith("/") else "/" + str(path)
            self.TES_url = f"{parsed.scheme}://{parsed.netloc}{path_str}"
        else:
            self.TES_url = TES_url

        if submission_url is None:
            parsed = urlparse(self.base_url)
            path = Path(parsed.path) / "api" / "Submission"
            # Ensure leading slash for URL path
            path_str = str(path) if str(path).startswith("/") else "/" + str(path)
            self.submission_url = f"{parsed.scheme}://{parsed.netloc}{path_str}"
        else:
            self.submission_url = submission_url

        ## this assumes that the docker image is the same for all tasks - could change the format like with tres to allow multiple with some separator
        ## but then we'd have to have some way to select the image for the task
        self.default_image = default_image or os.getenv("TES_DOCKER_IMAGE")
        if not self.default_image:
            raise ValueError("TES_DOCKER_IMAGE environment variable is required")

        default_db_port = default_db_port or os.getenv("postgresPort")
        # if not default_db_port:
        #    raise ValueError("DB_PORT environment variable is required")

        if default_db_config is None:
            db_host = os.getenv("postgresServer")
            #    if not db_host:
            #        raise ValueError("DB_HOST environment variable is required")

            db_username = os.getenv("postgresUsername")
            #    if not db_username:
            #        raise ValueError("DB_USERNAME environment variable is required")

            db_password = os.getenv("postgresPassword")
            #    if not db_password:
            #        raise ValueError("DB_PASSWORD environment variable is required")

            db_name = os.getenv("postgresDatabase")
            #    if not db_name:
            #        raise ValueError("DB_NAME environment variable is required")

            self.default_db_config = {
                "host": db_host,
                "username": db_username,
                "password": db_password,
                "name": db_name,
                "port": default_db_port,
                "schema": os.getenv("postgresSchema"),
            }
        else:
            self.default_db_config = default_db_config

        self.set_tags()
        self.task = None

    def set_tags(self, tres: List[str] = None) -> None:
        """
        Set the tags for a TES task. Tags are a class variable that is set when the client is initialized, but will also return the tags for consistency.
        """

        if tres is None:
            tres = os.getenv("5STES_TRES")
            if not tres:
                raise ValueError(
                    "5STES_TRES environment variable is required when tres parameter is not provided"
                )

        # Convert tres to list format for storage
        if isinstance(tres, list):
            tres_list = tres
        elif isinstance(tres, str):
            # If it's a string, parse it (could be comma or pipe separated)
            if "," in tres:
                tres_list = [tre.strip() for tre in tres.split(",") if tre.strip()]
            elif "|" in tres:
                tres_list = [tre.strip() for tre in tres.split("|") if tre.strip()]
            else:
                tres_list = [tres.strip()] if tres.strip() else []
        else:
            raise ValueError(f"tres must be a list or string, got {type(tres)}")

        tags = Tags(
            {
                "Project": os.getenv("5STES_PROJECT"),
                "tres": tres_list,  # Store as list
            }
        )
        self.tags = tags

    def _build_api_url(
        self, base_url: str, endpoint: str, query_params: Dict[str, str] = None
    ) -> str:
        """
        Build a complete API URL with proper path joining and query parameters.

        Args:
            base_url (str): Base URL
            endpoint (str): API endpoint
            query_params (Dict[str, str], optional): Query parameters to add

        Returns:
            str: Complete API URL
        """
        # Use pathlib to join URL paths
        parsed = urlparse(base_url)
        path = Path(parsed.path) / endpoint
        url = f"{parsed.scheme}://{parsed.netloc}{path}"

        if query_params:
            from urllib.parse import urlencode

            query_string = urlencode(query_params)
            url = f"{url}?{query_string}"

        return url

    ########################################################
    @abstractmethod
    def set_inputs(self, *args, **kwargs) -> None:
        """
        Set the inputs for a TES task.
        Subclasses can define their own parameters.
        """
        pass

    @abstractmethod
    def set_outputs(self, *args, **kwargs) -> None:
        """
        Set the outputs for a TES task.
        Subclasses can define their own parameters.
        Examples:
        - set_outputs() -> List[Output]
        - set_outputs(name: str, output_path: str) -> Output
        """
        pass

    @abstractmethod
    def set_executors(self, *args, **kwargs) -> None:
        """
        Set the executors for a TES task.
        Subclasses can define their own parameters.
        """
        pass

    @abstractmethod
    def set_tes_messages(self, *args, **kwargs) -> None:
        """
        Set the TES messages for a TES task. Typically will call set_inputs, set_outputs, and set_executors.
        Subclasses can define their own parameters.
        """
        pass

    ########################################################

    def create_tes_message(
        self, task_name: str = "analysis test", task_description: str = ""
    ) -> tes.Task:
        """
        Create a TES message JSON configuration.

        Args:
            task_name: str
            task_description: str
            inputs: tes.Input
            outputs: tes.Output
            executors: Union[tes.Executor, List[tes.Executor]] - Single executor or list of executors
        """

        self.task = tes.Task(
            name=task_name,
            description=task_description,
            inputs=self.inputs,
            outputs=self.outputs,
            executors=self.executors,
        )
        return self.task

    def create_FiveSAFES_TES_message(self, task: tes.Task = None) -> tes.Task:
        """
        Create a 5SAFE TES message JSON configuration.
        """
        if task is None and self.task is None:
            task = self.create_tes_message()
        elif task is None:
            task = self.task
        if task.tags is None:
            task.tags = {}
        # Convert tres list to pipe-separated string for py-tes compatibility
        tags_for_task = {
            "Project": self.tags["Project"],
            "tres": "|".join(self.tags["tres"])
            if isinstance(self.tags["tres"], list)
            else self.tags["tres"],
        }
        task.tags.update(tags_for_task)

        self.task = task
        return task

    def save_tes_task(self, task: Dict[str, Any], output_file: str):
        """
        Save the TES task configuration to a JSON file.

        Args:
            task (Dict[str, Any]): TES task configuration
            output_file (str): Path to save the JSON file
        """
        with open(output_file, "w") as f:
            json.dump(task, f, indent=4)

    def generate_curl_command(self, template: Dict[str, Any]) -> str:
        """
        Generate a curl command for submitting the template.

        Args:
            template (Dict[str, Any]): Submission template configuration

        Returns:
            str: Formatted curl command
        """
        # Convert template to JSON string with proper escaping
        template_json = json.dumps(template).replace('"', '\\"')

        tasks_url = self._build_api_url(self.TES_url, "tasks")
        curl_command = f"""curl -X 'POST' \\
  '{tasks_url}' \\
  -H 'accept: text/plain' \\
  -H 'Authorization: Bearer **TOKEN-HERE**' \\
  -H 'Content-Type: application/json' \\
  -d '{template_json}'"""

        return curl_command

    def submit_task(
        self,
        template: Union[Dict[str, Any], tes.Task],
        token_session: SubmissionAPISession,
    ) -> Dict[str, Any]:
        """
        Submit a TES task using the requests library.

        Args:
            template (Union[Dict[str, Any], tes.Task]): The TES task template or task object
            token (str): Authentication token

        Returns:
            Dict[str, Any]: Response from the server

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        if isinstance(template, tes.Task):
            template = template.as_dict()

        ### adds a description to the 5STES message
        template["description"] = "test"
        headers = {"accept": "text/plain", "Content-Type": "application/json"}

        try:
            tasks_url = self._build_api_url(self.TES_url, "tasks")

            response = token_session.request(
                method="POST", url=tasks_url, headers=headers, json=template
            )

            # Debug: Print response details for 400 errors
            if response.status_code == 400:
                print(f"400 Bad Request Response:")
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"Response Content: {response.text}")

            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error submitting task: {str(e)}")
            if hasattr(e.response, "text"):
                print(f"Response content: {e.response.text}")
            raise

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a submitted task.

        Args:
            task_id (str): Task ID

        Returns:
            Dict[str, Any]: Task status information
        """

        headers = {
            "accept": "text/plain"  # ,
            #'Authorization': f'Bearer {token}'
        }

        try:
            url = self._build_api_url(self.submission_url, f"GetASubmission/{task_id}")
            response = requests.get(url, headers=headers)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting task status: {str(e)}, retrying...")
            response = requests.get(url, headers=headers)
            return response.json()
            ## if it fails again, it will raise an exception
            # raise
