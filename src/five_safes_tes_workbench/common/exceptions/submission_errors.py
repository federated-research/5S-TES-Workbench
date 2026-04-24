from .base import WorkbenchError


class SubmissionError(WorkbenchError):
    """
    Raised when task submission to TES
    endpoint fails.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code

        full_message = f"\n Submission failed:\n\n  • {message}"
        if status_code:
            full_message += f"\n  • HTTP status: {status_code}"
        super().__init__(full_message)
