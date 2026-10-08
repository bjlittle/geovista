# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Render chosen ``sphinx-gallery`` examples as static images.

In a gallery build, :meth:`pyvista.Plotter.show` exports an interactive
``.vtksz`` scene for every plot, which costs build time and reader download in
proportion to the size of the scene. The examples in :data:`STATIC` skip that
export, and so their pages show the static image instead.

:func:`reset` is called by ``sphinx-gallery`` around each example, see the
``reset_modules`` option in ``conf.py``. It unregisters the ``trame`` plotter
component before a static example, which ``show`` takes to mean there is no
scene to export, and registers it again afterwards.

Notes
-----
.. versionadded:: 0.6.0

"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyvista as pv

import geovista.examples

__all__ = ["STATIC", "reset"]

COMPONENT: str = "trame"
"""The plotter component that exports the interactive scene."""

STATIC: frozenset[str] = frozenset(
    {
        "domain.clouds_robin",
        "grid.reykjanes",
        "grid.reykjanes_contour",
        "spatial_index.uber_h3",
        "unstructured.smc_sinu",
        "vector_data.wind_arrows_uvw",
    }
)
"""The examples rendered as a static image, rather than an interactive scene."""

# sphinx-gallery only gives the file name of an example, which is unique
EXAMPLES: dict[str, str] = {
    path.stem: ".".join(path.relative_to(root).with_suffix("").parts)
    for root in [Path(geovista.examples.__file__).parent]
    for path in root.rglob("*.py")
    if path.stem != "__init__"
}
"""The qualified name of each example, keyed by its file name stem."""

_component: type | None = None


def _registered() -> type | None:
    """Return the registered ``trame`` plotter component, if any."""
    for item in pv.registered_plotter_components():
        if item.name == COMPONENT:
            return item.component
    return None


def _enable() -> None:
    """Ensure the ``trame`` plotter component is registered."""
    if _registered() is None and _component is not None:
        pv.register_plotter_component(COMPONENT)(_component)


def _disable() -> None:
    """Ensure the ``trame`` plotter component is not registered."""
    global _component  # noqa: PLW0603

    if (component := _registered()) is not None:
        _component = component
        pv.unregister_plotter_component(COMPONENT)


def reset(gallery_conf: dict[str, Any], fname: str | None, when: str) -> None:  # noqa: ARG001
    """Prepare the plotter components before or after an example.

    Parameters
    ----------
    gallery_conf : dict
        The ``sphinx-gallery`` configuration.
    fname : str or None
        The file name of the example.
    when : str
        Either ``"before"`` or ``"after"`` the example is run.

    """
    name = EXAMPLES.get(Path(fname).stem) if fname else None

    if when == "before" and name in STATIC:
        _disable()
    else:
        _enable()
