from datetime import datetime, timezone

import tes  # type: ignore

from ...common.exceptions.tes_error import TESBuildError
from ...common.params.tes_builder_params import TESTaskParams
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
                "Call build_tes.hello_world() or build_tes.custom() first."
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

        image = params["image"]
        command = params["command"]
        name = params["name"]
        description = params["description"]
        output_url = params["output_url"]
        output_path = params["output_path"]

        self._tes_task = tes.Task(
            name=name,
            description=description,
            inputs=[],
            outputs=[
                tes.Output(
                    name="Stdout",
                    description="Stdout results",
                    url=output_url,
                    path=output_path,
                    type="DIRECTORY",
                )
            ],
            executors=[tes.Executor(image=image, command=command)],
            volumes=None,
            tags={
                "project": config.project,
                "tres": ",".join(config.tres),
            },
            logs=None,
            creation_time=datetime.now(timezone.utc),
        )

        task_json_pretty: str = self._tes_task.as_json(indent=3)  # type: ignore[reportUnknownMemberType]
        logger.info("TES Task built successfully")
        logger.info("TES payload:\n%s", task_json_pretty)
