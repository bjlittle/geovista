# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Convenience functions to access, download and cache :mod:`geovista` resources.

Notes
-----
.. versionadded:: 0.1.0

"""

from __future__ import annotations

from functools import wraps
import os
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, AnyStr, TypeAlias

import pooch

from geovista.config import resources

__all__ = [
    "BASE_URL",
    "CACHE",
    "DATA_VERSION",
    "GEOVISTA_CACHEDIR",
    "GEOVISTA_DATA_VERSION",
    "GEOVISTA_POOCH_MUTE",
    "RETRY_ATTEMPTS",
    "pooch_mute",
    "reload_registry",
]

if TYPE_CHECKING:
    from collections.abc import Callable

# this is a type alias
FileLike: TypeAlias = str | IO[AnyStr]
"""Type alias for filename or file-like object."""

BASE_URL: str = "https://github.com/bjlittle/geovista-data/raw/{version}/assets/"
"""Base URL for :mod:`geovista` resources."""

DATA_VERSION: str = "2025.03.9"
"""The ``geovista-data`` repository version for :mod:`geovista` resources."""

GEOVISTA_CACHEDIR: str = "GEOVISTA_CACHEDIR"
"""Environment variable to override :mod:`pooch` cache manager path."""

GEOVISTA_DATA_VERSION: str = os.environ.get("GEOVISTA_DATA_VERSION", DATA_VERSION)
"""Environment variable to override default :attr:`DATA_VERSION`."""

RETRY_ATTEMPTS: int = 3
"""The number of retry attempts to download a resource."""

URL_DKRZ_FESOM: str = (
    "https://swift.dkrz.de/v1/dkrz_0262ea1f00e34439850f3f1d71817205/FESOM/"
    "tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc"
)

CACHE: pooch.Pooch = pooch.create(
    path=resources["cache_dir"],
    base_url=BASE_URL,
    version=GEOVISTA_DATA_VERSION,
    version_dev="main",
    registry=None,
    retry_if_failed=RETRY_ATTEMPTS,
    env=GEOVISTA_CACHEDIR,
    urls={
        "tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc": URL_DKRZ_FESOM  # noqa: E501
    },
)
"""Cache manager for :mod:`geovista` resources."""

GEOVISTA_POOCH_MUTE: bool = (
    os.environ.get("GEOVISTA_POOCH_MUTE", "false").lower() == "true"
)
"""Verbosity status of the :mod:`pooch` cache manager logger."""


# configure the cache with the registry
with (Path(__file__).parent / "registry.txt").open(
    "r", encoding="utf-8", errors="strict"
) as text_io:
    CACHE.load_registry(text_io)

# maintain the original Pooch.fetch method prior to wrapping
# with user-agent headers version
CACHE._fetch = CACHE.fetch  # noqa: SLF001


@wraps(CACHE._fetch)  # noqa: SLF001
def _fetch(
    *args: str, **kwargs: bool | Callable[..., Any]
) -> str:  # numpydoc ignore=GL08
    # default to our http/s downloader with user-agent headers
    kwargs.setdefault("downloader", _downloader)
    result: str = CACHE._fetch(*args, **kwargs)  # noqa: SLF001
    return result


# override the original Pooch.fetch method with our
# user-agent headers version
CACHE.fetch = _fetch


def _downloader(
    url: str,
    output_file: FileLike[Any],
    poocher: pooch.Pooch,
    check_only: bool | None = False,
) -> bool | None:
    """Download the `url` asset over HTTP/S to the target file.

    Uses :func:`requests.get` with ``User-Agent`` configured
    within the request headers.

    Parameters
    ----------
    url : str
        The URL of the asset to be downloaded.
    output_file : FileLike
        The target file for the asset.
    poocher : Pooch
        The :class:`~pooch.Pooch` instance requesting the asset download.
    check_only : bool, optional
        If ``True``, will only check if the asset exists on the server
        without downloading it. Will return ``True`` if the asset exists
        and ``False`` otherwise.

    Returns
    -------
    bool or None
        If `check_only` is ``True``, returns a boolean indicating whether
        the requested asset is available. Otherwise, returns ``None``.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    import geovista

    # see https://github.com/readthedocs/readthedocs.org/issues/11763
    headers = {"User-Agent": f"geovista ({geovista.__version__})"}
    downloader: Callable[..., bool | None] = pooch.HTTPDownloader(headers=headers)
    return downloader(url, output_file, poocher, check_only=check_only)


def pooch_mute(silent: bool | None = None) -> bool:
    """Control the :mod:`pooch` cache manager logger verbosity.

    Updates the status variable :data:`GEOVISTA_POOCH_MUTE`.

    Parameters
    ----------
    silent : bool, optional
        Whether to silence or activate the :mod:`pooch` cache manager logger messages
        to the console. Defaults to ``True``.

    Returns
    -------
    bool
        The previous value of :data:`GEOVISTA_POOCH_MUTE`.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    global GEOVISTA_POOCH_MUTE  # noqa: PLW0603

    if silent is None:
        silent = True

    level = "WARNING" if silent else "NOTSET"
    pooch.utils.get_logger().setLevel(level)
    original = GEOVISTA_POOCH_MUTE
    GEOVISTA_POOCH_MUTE = silent
    return original


def reload_registry(fname: str | None = None) -> None:
    """Refresh the registry of the :data:`CACHE`.

    See :meth:`pooch.Pooch.load_registry` for more details.

    Parameters
    ----------
    fname : str, optional
        The filename of the registry to be loaded. If ``None``, defaults to
        the ``cache/registry.txt`` resource file packaged with :mod:`geovista`.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    if fname is None:
        text_io = (Path(__file__).parent / "registry.txt").open(
            "r", encoding="utf-8", errors="strict"
        )
    CACHE.load_registry(text_io)


# configure the pooch cache manager logger verbosity
pooch_mute(GEOVISTA_POOCH_MUTE)
