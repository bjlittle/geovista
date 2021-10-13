"""
A package for provisioning common geovista infrastructure.

"""
from typing import Optional

import pyvista as pv

from .logger import get_logger

__all__ = [
    "set_jupyter_backend",
]

# configure the logger
logger = get_logger(__name__)

#
# TODO: support richer default management
#

#: Default jupyter plotting backend for pyvista.
JUPYTER_BACKEND: bool = "ipygany"


def active_kernel() -> bool:
    """
    .. versionadded:: 0.1.0

    Determine whether we are executing within an ``IPython`` kernel.

    Returns
    -------
    bool

    """
    result = True
    try:
        from IPython import get_ipython

        ip = get_ipython()
        ip.kernel
    except (AttributeError, ModuleNotFoundError):
        result = False
    return result


def set_jupyter_backend(backend: Optional[str] = None) -> bool:
    """
    .. versionadded:: 0.1.0

    Configure the jupyter plotting backend for pyvista.

    Parameters
    ----------
    backend : str or None, default=None
        The pyvista plotting backend. For further details see :func:`pyvista.set_jupyter_backend`.
        If ``None``, default to :data:`JUPYTER_BACKEND`.

    Returns
    -------
    bool
        Whether the jupyter backend was successfully configured.

    """
    result = False
    if active_kernel():
        try:
            if backend is None:
                backend = JUPYTER_BACKEND
            pv.set_jupyter_backend(backend)
            result = True
        except ImportError:
            logger.info(f"Unable to set the pyvista jupyter backend to {backend!r}")
    else:
        logger.debug("No active IPython kernel available")

    return result
