from .base import WorkbenchError


class AuthValidationError(WorkbenchError):
    """
    Raised when authentication configuration
    validation fails.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors

        message = self._format(errors)
        super().__init__(message)

    @staticmethod
    def _format(errors: list[str]) -> str:

        header = "\n Auth validation failed:\n"
        body = "\n".join(f"  • {e}" for e in errors)
        return f"{header}\n{body}"
