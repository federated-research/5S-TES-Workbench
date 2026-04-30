from .base import WorkbenchError


class TESBuildError(WorkbenchError):
    """
    Raised when there is an error building a
    TES template or task.
    """

    pass


class DuplicateTemplateError(WorkbenchError):
    """
    Raised when attempting to register a template
    with a name that already exists.
    """

    pass
