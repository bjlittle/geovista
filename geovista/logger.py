"""
A package for provisioning logging infra-structure.

"""

import logging
from typing import Optional, Union

__all__ = ["DATEFMT", "FMT", "Formatter", "get_logger"]


#: The default ``datefmt`` string of the logger formatter.
DATEFMT: str = "%d-%m-%Y %H:%M:%S"

#: The default ``fmt`` string of the logger formatter.
FMT: str = "%(asctime)s %(name)s %(levelname)s - %(message)s"


class Formatter(logging.Formatter):
    """
    .. versionadded:: 0.1.0

    A :class:`logging.Formatter` that always appends the class name,
    if available, and the function name to a logging message.

    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        fmt : str, optional
            The format string of the :class:`logging.Formatter`.
            If ``None``, defaults to :data:`FMT`.
        datefmt : str, optional
            The date format string of the :class:`logging.Formatter`.
            If ``None``, defaults to :data:`DATEFMT`.

        """
        if fmt is None:
            fmt = FMT
        if datefmt is None:
            datefmt = DATEFMT
        super().__init__(fmt=fmt, datefmt=datefmt, style="%")

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the provided record into a logging message.

        Parameters
        ----------
        record : LogRecord
            The :class:`logging.LogRecord` that requires to be formatted.

        Returns
        -------
        str
            The formatted message of the log record.

        """
        result = super().format(record)
        if "cls" in record.__dict__:
            extra = "[%(cls)s.%(funcName)s]"
        else:
            extra = "[%(funcName)s]"
        result = f"{result} {extra % record.__dict__}"
        return result


def get_logger(name: str, level: Optional[Union[int, str]] = None) -> logging.Logger:
    """
    .. versionadded:: 0.1.0

    Create and configure a :class:`logging.Logger`.

    Child loggers will simply propagate their messages to the singleton root
    logger in the logging hierarchy, or the first parent logger with a handler
    configured.

    The root logger, if specified, will be configured with a
    :class:`logging.StreamHandler` and a custom :class:`Formatter`, as will the
    top-level ``geovista`` logger.

    Parameters
    ----------
    name : str
        The name of the logger. Typically this is the module filename
        (``__name__``) that owns the logger. Note that, the singleton root
        logger is selected with a ``name`` of ``None`` or ``root``.
    level : int or str, optional
        The threshold level of the logger. If ``None``, defaults to ``WARNING``
        for the ``root`` logger, ``NOTSET`` for the top-level logger, ``INFO``
        otherwise.

    Returns
    -------
    logging.Logger
        A configured :class:`logging.Logger`.

    """
    # Determine if this is the root logger.
    root = name is None or name == "root"

    # Determine if this is the top-level logger.
    top = name == __package__

    if level is None:
        level = "WARNING" if root else "NOTSET" if top else "INFO"

    # Create the named logger.
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not root:
        # Children propagate to the top-level logger.
        logger.propagate = not top

    # Create and add the handler, if required.
    if root or top:
        # Create a logging handler.
        handler = logging.StreamHandler()
        # Set the custom formatter.
        handler.setFormatter(Formatter())
        # Add the handler to the logger.
        logger.addHandler(handler)

    return logger
