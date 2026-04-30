from typing import Any

from ...common.exceptions.tes_error import DuplicateTemplateError, TESBuildError
from ...common.params.tes_builder_params import TESTaskParams
from ...utils.logger import get_logger
from ..base.tes_template_abc import BaseTESTemplate

logger = get_logger(__name__)


class BaseTemplateRegistry:
    """
    Registry for TES task templates.
    Handles registration, lookup, and parameter merging.
    """

    def __init__(self) -> None:
        """
        Initializes an empty template registry.
        """
        self._templates: dict[str, BaseTESTemplate[Any]] = {}

    @property
    def available(self) -> list[str]:
        """
        Returns a list of available template names
        in the registry.
        """
        return list(self._templates.keys())

    def register(self, template: BaseTESTemplate[Any]) -> None:
        """
        Registers a new template. Raises DuplicateTemplateError
        if a template with the same name already exists.
        """
        if template.name in self._templates:
            raise DuplicateTemplateError(
                f"A template named '{template.name}' is already registered. "
                "Please use a different name."
            )
        self._templates[template.name] = template
        logger.info("Template registered: '%s'", template.name)

    def resolve(
        self,
        template_name: str,
        overrides: dict[str, object] | None = None,
    ) -> TESTaskParams:
        """
        Resolves a template by name, delegating to the
        template's own resolve() with the provided overrides.

        Raises TESBuildError if the template is not found.
        """
        template = self._get(template_name)
        logger.info("Resolving template: '%s'", template_name)
        return template.resolve(overrides or {})

    def _get(self, name: str) -> BaseTESTemplate[Any]:
        """
        Retrieves a template by name. Raises
        TESBuildError if not found.
        """
        if name not in self._templates:
            available = ", ".join(self._templates.keys())
            raise TESBuildError(
                f"Template '{name}' not found. Available templates: [{available}]"
            )
        return self._templates[name]
