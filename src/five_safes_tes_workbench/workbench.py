from pathlib import Path
from typing import Unpack

from .common.params.validate_params import ConfigValidationParams
from .core.builders.submit_builder import WorkbenchSubmit
from .core.builders.tes_builder import WorkbenchTESBuilder
from .core.builders.validate_builder import WorkbenchValidateBuilder
from .core.minio.minio_client import MinioClientBuilder
from .helpers.children_task import (
    get_child_task_info,
    is_child_task_completed,
)
from .services.tes_builder_service import TESBuilderService


class Workbench:
    """
    Main class for the Five Safes TES Workbench.

    Process
    -------
    This class holds the main methods as follows:

    1. validate: Validates the configuration.
    2. build_tes: Builds the TES task.
    3. submit: Submits the TES task to the endpoint.
    """

    def __init__(
        self,
        validator: WorkbenchValidateBuilder | None = None,
        task_builder: WorkbenchTESBuilder | None = None,
        submitter: WorkbenchSubmit | None = None,
    ) -> None:
        """
        Initializes the Workbench with instances of the
        validate builder, TES builder, and submit builder.
        """
        self._validator = validator or WorkbenchValidateBuilder()
        self._task_builder = task_builder or WorkbenchTESBuilder()
        self._submitter = submitter or WorkbenchSubmit()
        self._last_task_id: str | None = None

    # ----- Validation Builder -----

    def validate(
        self,
        config_path: str | None = None,
        **kwargs: Unpack[ConfigValidationParams],
    ) -> "Workbench":
        """
        Validates the configuration and
        authentication parameters.

        Parameters
        ----------
        - config_path: Optional path to the configuration file.
        - kwargs: Parameters for validation.
        """
        self._validator.validate(config_path, **kwargs)
        return self

    # ----- TES Builder -----

    @property
    def build_tes(self) -> TESBuilderService:
        """
        Provides access to TES building methods.

        It uses dynamic attribute access to allow template-based
        building via method calls (e.g., `build_tes.hello_world()`)
        and a custom build method for fully user-defined tasks.

        Returns
        -------
        TESBuilderService: An instance that provides methods
        to build TES tasks.
        """
        return TESBuilderService(self._validator, self._task_builder)

    # ----- Submit Builder -----

    def submit(self) -> str:
        """
        Submits the built TES task to the
        configured TES endpoint.


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

    # ----- MinIO Results Command -----

    def fetch_outputs(
        self,
        tre: str | None = None,
        task_id: int | None = None,
        output_dir: Path | str | None = None,
    ) -> dict[str, list[Path]]:
        """
        Download all output objects for a completed TES task from MinIO to disk
        for every configured TRE.

        If a TRE is specified, only the output objects for that TRE are downloaded.
        If no TRE is specified, all output objects for all TREs are downloaded.

        Files are saved under ``<output_dir>/<tre>/<filename>`` where
        ``output_dir`` defaults to an ``output/`` folder created next to
        the calling notebook (i.e. ``Path.cwd() / "output"``).

        Authentication is re-used from the earlier :meth:`validate` call.
        Credentials are exchanged at the configured STS endpoint so that a
        temporary MinIO session is obtained automatically.

        Parameters
        ----------
        - tre: Name of the TRE whose results to retrieve. If not specified, all TREs are retrieved.
        - task_id: ID of the task whose results to retrieve. Defaults to
          the ID returned by the most recent :meth:`submit` call.
        - output_dir: Root directory for downloads. Each TRE gets its own
          sub-folder ``<output_dir>/<tre>/``. Defaults to
          ``Path.cwd() / "output" / <tre> / <task_id>``.

        Returns
        -------
        Dict mapping each TRE name to the list of
        :class:`~pathlib.Path` objects for its downloaded files.
        """
        resolved_id = str(task_id) if task_id is not None else self._last_task_id
        print("resolved_id", resolved_id)
        if resolved_id is None:
            raise ValueError(
                "No Submission task ID available. Either call submit() first or pass "
                "a task_id explicitly to fetch_all_results()."
            )

        results: dict[str, list[Path]] = {}

        minio_client = MinioClientBuilder(
            config=self._validator.config,
            auth=self._validator.auth,
        )

        if tre is not None:
            if tre not in self._validator.config.tres:
                raise ValueError(
                    f"TRE {tre} not found in the configuration. Please specify a valid TRE."
                )
            child_task_info = get_child_task_info(
                self._validator.config, resolved_id, tre
            )

            if not is_child_task_completed(child_task_info):
                results[tre] = []

            resolved_output_dir = (
                Path(output_dir)
                if output_dir is not None
                else Path.cwd() / "output" / tre / str(child_task_info.id)
            )
            results[tre] = minio_client.download_results(
                child_task_info.id, resolved_output_dir
            )
            return results
        else:
            for tre_in_config in self._validator.config.tres:
                child_task_info = get_child_task_info(
                    self._validator.config, resolved_id, tre_in_config
                )
                if not is_child_task_completed(child_task_info):
                    continue

                resolved_output_dir = (
                    Path(output_dir)
                    if output_dir is not None
                    else Path.cwd() / "output" / tre_in_config / str(child_task_info.id)
                )
                results[tre_in_config] = minio_client.download_results(
                    child_task_info.id, resolved_output_dir
                )

        return results
