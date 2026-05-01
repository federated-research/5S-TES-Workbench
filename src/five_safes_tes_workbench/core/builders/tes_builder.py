from datetime import datetime, timezone

import tes  # type: ignore

from ...common.exceptions.tes_error import TESBuildError
from ...common.params.tes_builder_params import (
    ExecutorTESParams,
    InputTESParams,
    OutputTESParams,
    TESTaskParams,
)
from ...core.tes.base_registry import BaseTemplateRegistry
from ...core.tes.registry import create_default_registry
from ...schema.config_schema import ConfigValidationModel
from ...utils.logger import get_logger

logger = get_logger(__name__)


class WorkbenchTESBuilder:
    """
    Builder class responsible for constructing TES tasks.

    Supports two modes:
        1. Template-based: build_from_template() — uses registered
           templates with optional overrides.
        2. Custom: build() — fully user-defined parameters.

    Attributes:
        _tes_task: The constructed TES task.
        _registry: Template registry for preset tasks.
    """

    def __init__(
        self,
        registry: BaseTemplateRegistry | None = None,
    ) -> None:
        self._tes_task: tes.Task | None = None
        self._registry = registry or create_default_registry()

    @property
    def tes_task(self) -> tes.Task:
        if self._tes_task is None:
            raise TESBuildError(
                "No TES task has been built. "
                "Call build_from_template() or build() first."
            )
        return self._tes_task

    def build_from_template(
        self,
        config: ConfigValidationModel,
        template_name: str,
        overrides: dict[str, object] | None = None,
    ) -> None:
        """
        Builds a TES task from a registered template.
        Registry handles lookup and parameter merging.

        Args:
            config: Validated infrastructure configuration.
            template_name: Name of the template.
            overrides: Optional params to override template defaults.
        """
        params = self._registry.resolve(template_name, overrides)
        self.build(config, params)

    def build(
        self,
        config: ConfigValidationModel,
        params: TESTaskParams,
    ) -> None:
        """
        Builds a TES task from provided parameters.
        All values must come from template or user params.

        Args:
            config: Validated infrastructure configuration.
            params: TES task parameters.
        """

        name = params["name"]
        executors = self._build_executors(params["executors"])
        inputs = self._build_inputs(params.get("inputs", []) or [])
        outputs = self._build_outputs(params.get("outputs", []) or [])
        description = params.get("description")
        volumes = params.get("volumes")

        self._tes_task = tes.Task(
            name=name,
            description=description,
            inputs=inputs or None,
            outputs=outputs or None,
            executors=executors,
            volumes=volumes,
            tags={
                "project": config.project,
                "tres": "|".join(config.tres),
            },
            logs=None,
            creation_time=datetime.now(timezone.utc),
        )

        task_json_pretty: str = self._tes_task.as_json(indent=3)  # type: ignore[reportUnknownMemberType]
        logger.info("TES Task built successfully")
        logger.info("TES payload:\n%s", task_json_pretty)

    @staticmethod
    def _build_executors(
        executors: list[ExecutorTESParams],
    ) -> list[tes.Executor]:
        """
        Converts a list of ExecutorTESParams into tes.Executor objects.
        Raises TESBuildError if no executors are provided.
        """
        if not executors:
            raise TESBuildError(
                "At least one executor is required to build a TES task."
            )

        return [
            tes.Executor(
                image=executor["image"],
                command=executor["command"],
                workdir=executor.get("workdir"),
                stdin=executor.get("stdin"),
                stdout=executor.get("stdout"),
                stderr=executor.get("stderr"),
                env=executor.get("env"),
                ignore_error=executor.get("ignore_error"),
            )
            for executor in executors
        ]

    @staticmethod
    def _build_inputs(
        inputs: list[InputTESParams],
    ) -> list[tes.Input]:
        """
        Converts a list of InputTESParams into tes.Input objects.
        """
        return [
            tes.Input(
                name=input.get("name"),
                description=input.get("description"),
                url=input.get("url"),
                path=input["path"],
                type=input.get("type", "DIRECTORY"),
                content=input.get("content"),
                streamable=input.get("streamable"),
            )
            for input in inputs
        ]

    @staticmethod
    def _build_outputs(
        outputs: list[OutputTESParams],
    ) -> list[tes.Output]:
        """
        Converts a list of OutputTESParams into tes.Output objects.
        """
        return [
            tes.Output(
                name=output.get("name"),
                description=output.get("description"),
                url=output["url"],
                path=output["path"],
                type=output.get("type", "DIRECTORY"),
                path_prefix=output.get("path_prefix"),
            )
            for output in outputs
        ]
