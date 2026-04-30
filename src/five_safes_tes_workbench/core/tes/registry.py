from typing import Any

from ..base.tes_template_abc import BaseTESTemplate
from .base_registry import BaseTemplateRegistry
from .templates.custom import CustomTemplate
from .templates.hello_world import HelloWorldTemplate
from .templates.simple_sql import SimpleSQLTemplate

# ------ REGISTRY FACTORY ------

# This file defines the BaseTemplateRegistry class and a factory function
# to create a registry pre-populated with built-in templates.

# ---- Steps to add a new template: ----
# -------------------------------------------

# 1. Add a typed UserParams dict for the template if needed.
# 2. Create a new template class in the appropriate file.
# 3. Add the new template class to the _DEFAULT_TEMPLATES list.

# ------ List of built-in templates ------

_DEFAULT_TEMPLATES: list[type[BaseTESTemplate[Any]]] = [
    HelloWorldTemplate,
    CustomTemplate,
    SimpleSQLTemplate,

    # --- Add new templates above ---
]


def create_default_registry(
    templates: list[type[BaseTESTemplate[Any]]] | None = None,
) -> BaseTemplateRegistry:
    """
    Creates a registry with all built-in templates.

    Parameters
    ----------
        templates: Optional list of template classes to register.
                   Defaults to all built-in templates.
    """
    registry = BaseTemplateRegistry()

    for template_cls in templates or _DEFAULT_TEMPLATES:
        registry.register(template_cls())

    return registry
