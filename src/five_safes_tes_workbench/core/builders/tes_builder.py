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
                image=ex["image"],
                command=ex["command"],
                workdir=ex.get("workdir"),
                stdin=ex.get("stdin"),
                stdout=ex.get("stdout"),
                stderr=ex.get("stderr"),
                env=ex.get("env"),
                ignore_error=ex.get("ignore_error"),
            )
            for ex in executors
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
                name=i.get("name"),
                description=i.get("description"),
                url=i.get("url"),
                path=i["path"],
                type=i.get("type", "DIRECTORY"),
                content=i.get("content"),
                streamable=i.get("streamable"),
            )
            for i in inputs
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
                name=o.get("name"),
                description=o.get("description"),
                url=o["url"],
                path=o["path"],
                type=o.get("type", "DIRECTORY"),
                path_prefix=o.get("path_prefix"),
            )
            for o in outputs
        ]
