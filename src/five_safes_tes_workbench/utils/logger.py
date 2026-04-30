import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Utility function to get a logger with a consistent format.

    Parameters
    ----------
    - name: The name of the logger, typically __name__ of the module.

    Returns
    -------
    - A configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(levelname)s | %(message)s",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
