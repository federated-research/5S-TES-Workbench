import time
import os
import tes  # type: ignore
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

from five_safes_tes_workbench.clients.base_tes_client import BaseTESClient
from five_safes_tes_workbench.clients.minio_client import MinIOClient
from five_safes_tes_workbench.services.submission_polling_service import Polling
from five_safes_tes_workbench.auth.submission_api_session import SubmissionAPISession


load_dotenv()


class AnalysisOrchestrator:
    """
    Generic orchestrator class for TES task management.
    Handles task submission, polling, and result collection.
    Analysis-specific logic is handled by the AnalysisRunner class.
    """

    def __init__(
        self,
        tes_client: BaseTESClient,
        token_session: SubmissionAPISession,
        project: str = None,
    ):
        """
        Initialize the analysis orchestrator.

        Args:
            tes_client (BaseTESClient): TES client instance
            token (str): Authentication token for TRE-FX services
            project (str): Project name for TES tasks (defaults to 5STES_PROJECT env var)
        """
        if project is None:
            project = os.getenv("5STES_PROJECT")
            if not project:
                raise ValueError(
                    "5STES_PROJECT environment variable is required when project parameter is not provided"
                )

        self.token_session = token_session
        self.project = project
        self.tes_client = tes_client
        ## set to None here to be explicitly set later, either by passing args or environment variables
        self.tres = None
        self.minio_client = MinIOClient(token_session=token_session)

    def parse_tres(self, tres: str) -> List[str]:
        """
        Parse the TREs from the environment variable.
        """
        return [tre.strip() for tre in tres.split(",") if tre.strip()]

    def setup_analysis(
        self,
        analysis_type: str,
        task_name: str = None,
        task_description: str = None,
        bucket: str = None,
        tres: List[str] = None,
    ) -> Tuple[str, str, str, List[str]]:
        """
        Set up common analysis parameters.

        Args:
            analysis_type (str): Type of analysis to perform
            task_name (str, optional): Name for the TES task
            task_description (str, optional): Description for the TES task
            bucket (str, optional): MinIO bucket for outputs
            tres (List[str], optional): List of TREs to run analysis on

        Returns:
            Tuple[str, str, str, List[str]]: (task_name, task_description, bucket, tres)
        """
        # Set default task name based on analysis type if not provided
        if task_name is None:
            task_name = f"analysis {analysis_type}"
        if task_description is None:
            task_description = f"analysis {analysis_type} description"
        # Set default bucket from environment variable if not provided
        if bucket is None:
            bucket = os.getenv("MINIO_OUTPUT_BUCKET")
            if not bucket:
                raise ValueError(
                    "MINIO_OUTPUT_BUCKET environment variable is required when bucket parameter is not provided"
                )

        if tres is None:
            tres_env = os.getenv("5STES_TRES")
            if not tres_env:
                raise ValueError(
                    "5STES_TRES environment variable is required when tres parameter is not provided"
                )
            tres = self.parse_tres(tres_env)

        self.tres = tres
        return task_name, task_description, bucket, tres

    def _submit_and_collect_results(
        self,
        tes_message: tes.Task,
        bucket: str,
        output_format: str = "json",
        submit_message: str = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Common workflow: submit TES task, poll for results, and collect data.
        Used by both analytics and bunny analysis types.

        Args:
            tes_message (tes.Task): TES task message to submit
            bucket (str): MinIO bucket for outputs
            output_format (str): Output file format (default: "json")
            submit_message (str, optional): Custom message to print when submitting

        Returns:
            Tuple[str, List[Dict[str, Any]]]: (task_id, collected_data)
        """
        n_results = len(self.tres)

        if submit_message:
            print(submit_message)
        else:
            print(f"Submitting task to {n_results} TREs...")

        result = self.tes_client.submit_task(
            tes_message, token_session=self.token_session
        )

        task_id = result["id"]
        print(f"Task ID: {task_id}")

        results_paths = [
            f"{int(task_id) + i + 1}/output.{output_format}" for i in range(n_results)
        ]

        # Use polling engine to collect results
        polling_engine = Polling(self.tes_client, self.minio_client, task_id)
        data = polling_engine.poll_results(
            results_paths, bucket, n_results, polling_interval=10
        )

        return task_id, data

    def collect_results(
        self,
        task_id: str,
        token: str = None,
        bucket: str = None,
        output_format: str = "json",
    ):
        if token is None:
            token = os.getenv("5STES_TOKEN")
            if not token:
                raise ValueError(
                    "5STES_TOKEN environment variable is required when token parameter is not provided"
                )
        self.token = token
        if self.tres is None:
            tres = os.getenv("5STES_TRES")
            if not tres:
                raise ValueError(
                    "5STES_TRES environment variable is required when tres parameter is not provided"
                )
            self.tres = self.parse_tres(tres)
        if bucket is None:
            bucket = os.getenv("MINIO_OUTPUT_BUCKET")
            if not bucket:
                raise ValueError(
                    "MINIO_OUTPUT_BUCKET environment variable is required when bucket parameter is not provided"
                )
        n_results = len(self.tres)
        results_paths = [
            f"{int(task_id) + i + 1}/output.{output_format}" for i in range(n_results)
        ]
        return self._collect_results(results_paths, bucket, n_results)

    def _collect_results(
        self, results_paths: List[str], bucket: str, n_results: int
    ) -> List[str]:
        """
        Collect results from MinIO storage.

        Args:
            results_paths (List[str]): List of paths to collect results from
            bucket (str): MinIO bucket name
            n_results (int): Expected number of results

        Returns:
            List[str]: Collected data from all sources
        """
        data = []
        while len(data) < n_results:
            data = []
            for results_path in results_paths:
                result = self.minio_client.get_object(bucket, results_path)
                if result:
                    data.append(result)

            if len(data) < n_results:
                print(f"Waiting for results... ({len(data)}/{n_results} received)")
                time.sleep(10)

        print(f"{len(data)} results collected successfully")
        return data
