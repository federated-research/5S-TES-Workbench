from typing import Any, Unpack

from .core.validate_builder import WorkbenchValidateBuilder
from .core.tes_builder import WorkbenchTESBuilder
from .core.submit_builder import WorkbenchSubmitBuilder
from .core.minio_client import MinioClientBuilder
from .helpers.children_task import check_child_task_status, get_child_task_info
from .common.validate_params import ConfigValidationParams
from .common.tes_builder_params import TESTaskParams


class Workbench:
    """
    Main class for the Five Safes TES Workbench.

    Process
    -------
    This class holds the main methods as follows:

    1. validate: Validates the configuration and authentication.
    2. build_tes: Builds the TES task payload.
    3. submit: Submits the TES task to the endpoint and stores the task ID.
    4. fetch_results: Fetches task output objects from MinIO after the task
       has completed.
    """

    def __init__(self) -> None:
        """
        Initializes the Workbench with instances of the validate builder,
        TES builder, submit builder, and MinIO builder.
        """
        self._validator = WorkbenchValidateBuilder()
        self._task_builder = WorkbenchTESBuilder()
        self._submitter = WorkbenchSubmitBuilder()
        self._minio_client = MinioClientBuilder()
        self._last_task_id: str | None = None

    # ----- Validation Builder -----

    def validate(
        self,
        config_path: str | None = None,
        **kwargs: Unpack[ConfigValidationParams],
    ) -> "Workbench":
        """
        Validates the configuration and authentication parameters.

        Parameters
        ----------
        - config_path: Optional path to the configuration file.
        - kwargs: Parameters for validation.
        """
        self._validator.validate(config_path, **kwargs)
        return self

    # ----- TES Builder -----

    def build_tes(self, **kwargs: Unpack[TESTaskParams]) -> "Workbench":
        """
        Builds the TES message from the provided TES task parameters.

        Parameters
        ----------
        - kwargs: Parameters for building the TES task.
        """
        self._task_builder.build(
            self._validator.config,
            kwargs,
        )
        return self

    # ----- Submit Builder -----

    def submit(self) -> str:
        """
        Submits the built TES task to the configured TES endpoint.

        Returns
        -------
        The ID of the submitted task. The ID is also stored internally so
        that a subsequent :meth:`fetch_results` call can use it without
        requiring it to be passed explicitly.
        """
        task_id = self._submitter.submit(
            config=self._validator.config,
            auth=self._validator.auth,
            task=self._task_builder.tes_task,
        )
        self._last_task_id = task_id
        return task_id

    # ----- MinIO Results Commands -----

    def fetch_result_by_tre(
        self,
        task_id: str | None = None,
        tre: str | None = None,
        bucket: str | None = None,
    ) -> dict[str, Any]:
        """
        Fetch all output objects written by a completed TES task from MinIO.

        Authentication is re-used from the earlier :meth:`validate` call.
        Credentials are exchanged at the configured STS endpoint so that a
        temporary MinIO session is obtained automatically.

        Parameters
        ----------
        - task_id: ID of the task whose results to retrieve. Defaults to
          the ID returned by the most recent :meth:`submit` call.
        - tre: Name of the TRE to fetch the results for.
        - bucket: Override the output bucket from config. Defaults to
          ``config.minio_output_bucket``.

        Returns
        -------
        A dict mapping each result object path to its parsed content
        (JSON / CSV decoded where possible, raw string otherwise).
        """
        resolved_id = task_id or self._last_task_id
        if resolved_id is None:
            raise ValueError(
                "No Submission task ID available. Either call submit() first or pass "
                "a task_id explicitly to fetch_results()."
            )

        if tre is None:
            raise ValueError(
                "No TRE available. Please specify the TRE to fetch the results for."
            )
        if tre not in self._validator.config.tres:
            raise ValueError(
                f"TRE {tre} not found in the configuration. Please specify a valid TRE."
            )

        self._minio_client.initialise(
            config=self._validator.config,
            auth=self._validator.auth,
        )
        child_task_info = get_child_task_info(self._validator.config, resolved_id, tre)

        check_status_message = check_child_task_status(child_task_info)
        if check_status_message:
            return check_status_message
        return self._minio_client.fetch_result(child_task_info.id, bucket=bucket)

    def fetch_all_results(
        self,
        task_id: str | None = None,
        bucket: str | None = None,
    ) -> dict[str, Any]:
        """
        Fetch all output objects written by a completed TES task from MinIO.

        Authentication is re-used from the earlier :meth:`validate` call.
        Credentials are exchanged at the configured STS endpoint so that a
        temporary MinIO session is obtained automatically.

        Parameters
        ----------
        - task_id: ID of the task whose results to retrieve. Defaults to
          the ID returned by the most recent :meth:`submit` call.
        - tre: Name of the TRE to fetch the results for.
        - bucket: Override the output bucket from config. Defaults to
          ``config.minio_output_bucket``.

        Returns
        -------
        A dict mapping each result object path to its parsed content
        (JSON / CSV decoded where possible, raw string otherwise).
        """
        resolved_id = task_id or self._last_task_id
        if resolved_id is None:
            raise ValueError(
                "No Submission task ID available. Either call submit() first or pass "
                "a task_id explicitly to fetch_results()."
            )

        results: dict[str, dict[str, Any]] = {}

        self._minio_client.initialise(
            config=self._validator.config,
            auth=self._validator.auth,
        )
        for tre in self._validator.config.tres:
            child_task_info = get_child_task_info(
                self._validator.config, resolved_id, tre
            )
            check_status_message = check_child_task_status(child_task_info)
            if check_status_message:
                return check_status_message
            results[tre] = self._minio_client.fetch_result(
                child_task_info.id, bucket=bucket
            )

        return results
