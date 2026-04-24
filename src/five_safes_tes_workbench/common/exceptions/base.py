class WorkbenchError(Exception):
    """
    Base exception for all Five Safes
    TES Workbench errors.
    """

    def __init__(self, message: str) -> None:

        self.message = message
        super().__init__(message)
