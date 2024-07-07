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

import os
from pathlib import Path

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

BASE_URL: str = "https://github.com/bjlittle/geovista-data/raw/{version}/assets/"
"""Base URL for :mod:`geovista` resources."""

DATA_VERSION: str = "2024.07.0"
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

CACHE.load_registry(
    (Path(__file__).parent / "registry.txt").open(
        "r", encoding="utf-8", errors="strict"
    )
)

GEOVISTA_POOCH_MUTE: bool = (
    os.environ.get("GEOVISTA_POOCH_MUTE", "false").lower() == "true"
)
"""Verbosity status of the :mod:`pooch` cache manager logger."""


def pooch_mute(silent: bool = True) -> None:
    """Control the :mod:`pooch` cache manager logger verbosity.

    Updates the status variable :data:`GEOVISTA_POOCH_MUTE`.

    Parameters
    ----------
    silent : bool, optional
        Whether to silence or activate the :mod:`pooch` cache manager logger messages
        to the console.

    Notes
    -----
    .. versionadded:: 0.5.0

    """
    global GEOVISTA_POOCH_MUTE

    level = "WARNING" if silent else "NOTSET"
    pooch.utils.get_logger().setLevel(level)
    GEOVISTA_POOCH_MUTE = silent


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
        fname = (Path(__file__).parent / "registry.txt").open(
            "r", encoding="utf-8", errors="strict"
        )
    CACHE.load_registry(fname)


# configure the pooch cache manager logger verbosity
pooch_mute(GEOVISTA_POOCH_MUTE)
