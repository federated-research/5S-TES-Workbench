from __future__ import annotations

from ..common.exceptions.tes_error import TESBuildError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TESBuilderService:
    """
    Service class that provides interface for building
    TES tasks from templates.

    This class uses dynamic attribute access to allow
    users to call template names as methods.

    Example Usage
    -------------
    - `build_tes.hello_world(name="My Task", description="...")`

    - `build_tes.custom(name="Custom Task", description="...",
       image="...", command=["..."], output_url="...",
       output_path="...")`
    """

    def __init__(
        self,
        validator,
        task_builder,
    ) -> None:
        """
        Initializes the TESBuilderService with a
        validator and task builder.

        Parameters
        ----------
        - validator: Instance of ValidatorProtocol for
        config validation.
        - task_builder: Instance of TESBuilderProtocol
        for building TES tasks.
        """
        self._validator = validator
        self._task_builder = task_builder
        self._pending_template: str | None = None

    def __getattr__(self, name: str) -> TESBuilderService:
        """
        Auto-resolves template names as callable methods.
        Only intercepts non-private attribute lookups.
        """
        if name.startswith("_"):
            raise AttributeError(name)

        self._pending_template = name
        return self

    def __call__(self, **kwargs: object) -> TESBuilderService:
        """
        Builds TES task from the pending template
        with user-provided params.

        Parameters
        ----------
            **kwargs: Params defined by the template's UserParams.
        """
        pending = self._pending_template

        if pending is None:
            raise TESBuildError(
                "No template selected. Use build_tes.template_name() "
                "e.g. build_tes.hello_world() or build_tes.custom()"
            )

        logger.info("Building TES task from template: '%s'", pending)

        self._task_builder.build_from_template(
            self._validator.config,
            pending,
            kwargs,  # type: ignore[arg-type]
        )

        self._pending_template = None
        return self
