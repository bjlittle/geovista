"""Generate an environment report of the Python packages and GPU hardware resources.

Notes
-----
..versionadded:: 0.4.0

"""
from __future__ import annotations

from types import ModuleType
from typing import Union

import pyvista
import scooby

__all__ = ["Report"]

# type aliases
PackageLike = Union[ModuleType, str]

#: Default number of package columns in report HTML table.
NCOL: int = 3

#: The core packages of geovista to include in the environment report.
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

#: The optional packages of geovista to include in the environment report.
PACKAGES_OPTIONAL: list[str] = [
    "IPython",
    "PyQt5",
    "fastparquet",
    "imageio",
    "jupyter_server_proxy",
    "jupyterlab",
    "meshio",
    "nest_asyncio",
    "pandas",
    "pyvistaqt",
    "scipy",
    "trame",
    "trame_client",
    "trame_server",
    "trame_vtk",
    "tqdm",
]

#: Default text width of non-HTML report.
TEXT_WIDTH: int = 88


class Report(scooby.Report):
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
                extra_meta = pyvista.GPUInfo().get_info()
            except:
                # XXX: bare except required in order to handle rendering faults
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
