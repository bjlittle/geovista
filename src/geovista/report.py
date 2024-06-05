# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Generate an environment report of the Python packages and GPU hardware resources.

Notes
-----
.. versionadded:: 0.4.0

"""

from __future__ import annotations

from types import ModuleType
from typing import TypeAlias

import lazy_loader as lazy
import scooby

# lazy import third-party dependencies
pv = lazy.load("pyvista")

__all__ = [
    "NCOL",
    "PACKAGES_CORE",
    "PACKAGES_OPTIONAL",
    "PackageLike",
    "Report",
    "TEXT_WIDTH",
]

# type aliases
PackageLike: TypeAlias = ModuleType | str
"""Type alias for a package module or package name."""

# constants
NCOL: int = 3
"""Default number of package columns in report HTML table."""

PACKAGES_CORE: list[str] = [
    "cartopy",
    "click",
    "click-default-group",
    "cmocean",
    "colorcet",
    "geovista",
    "matplotlib",
    "netcdf4",
    "numpy",
    "platformdirs",
    "pooch",
    "pykdtree",
    "pyproj",
    "pyvista",
    "scooby",
    "vtk",
]
"""The core packages of geovista to include in the environment report."""

PACKAGES_OPTIONAL: list[str] = [
    "IPython",
    "PyQt5",
    "fastparquet",
    "imageio",
    "ipywidgets",
    "jupyter_server_proxy",
    "jupyterlab",
    "meshio",
    "nest_asyncio",
    "pandas",
    "pyvistaqt",
    "scipy",
    "trame",
    "trame_client",
    "trame_jupyter_extension",
    "trame_server",
    "trame_vtk",
    "trame_vuetify",
    "tqdm",
    "wslink",
]
"""The optional packages of geovista to include in the environment report."""

TEXT_WIDTH: int = 88
"""Default text width of non-HTML report."""


class Report(scooby.Report):  # numpydoc ignore=PR01
    """Generate an environment package and hardware report.

    Notes
    -----
    .. versionadded:: 0.4.0

    """

    def __init__(
        self,
        additional: PackageLike | list[PackageLike] | None = None,
        ncol: int | None = None,
        text_width: int | None = None,
        gpu: bool | None = True,
    ) -> None:
        """Generate an environment package and hardware report.

        Parameters
        ----------
        additional : PackageLike or list of PackageLike, optional
            Extra package modules or package names to include in the report.
        ncol : int, optional
            The number of package columns in a HTML table report. Defaults to
            :data:`NCOL`.
        text_width : int, optional
            The number of character columns in a non-HTML report. Defaults to
            :data:`TEXT_WIDTH`.
        gpu : bool, optional
            Detect GPU hardware details. Defaults to ``True``. Disable this option if
            experiencing rendering issues to ensure report generation.

        Notes
        -----
        .. versionadded:: 0.4.0

        """
        if ncol is None:
            ncol = NCOL

        if text_width is None:
            text_width = TEXT_WIDTH

        # mandatory packages
        core = PACKAGES_CORE

        # optional packages
        optional = PACKAGES_OPTIONAL

        # attempt to detect gpu hardware details
        if gpu:
            try:
                extra_meta = pv.GPUInfo().get_info()
            except:  # noqa: E722
                # bare except required in order to handle rendering faults
                extra_meta = [
                    ("GPU Details", "Error"),
                ]
        else:
            extra_meta = [
                ("GPU Details", "None"),
            ]

        super().__init__(
            additional=additional,
            core=core,
            optional=optional,
            ncol=ncol,
            text_width=text_width,
            extra_meta=extra_meta,
        )
