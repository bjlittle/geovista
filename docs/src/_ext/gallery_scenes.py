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

``sphinx-gallery`` skips an example whose source is unchanged since it was last
built, so :func:`reset` would never run for it. As an extension, this module
also invalidates the cache of each example whose membership of :data:`STATIC`
has changed since the previous build, see :func:`invalidate`.

Notes
-----
Unregistering the ``trame`` component is a workaround. Once ``pyvista`` only
exports a scene for a plot that is not rendered static, see
https://github.com/pyvista/pyvista/issues/9384, the examples in :data:`STATIC`
can use ``PYVISTA_GALLERY_FORCE_STATIC`` instead, and :func:`reset` and
:func:`invalidate` can go.

.. versionadded:: 0.6.0

"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

import pyvista as pv

import geovista.examples

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = ["STATIC", "invalidate", "reset", "setup"]

COMPONENT: str = "trame"
"""The plotter component that exports the interactive scene."""

STATE: str = ".gallery_scenes.json"
"""The record of the static examples within the gallery output of a build."""

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


def invalidate(gallery_dir: Path, static: frozenset[str] | None = None) -> list[str]:
    """Invalidate each cached example whose membership of the static set changed.

    Removing the cached checksum of an example makes ``sphinx-gallery`` run it
    again, and so :func:`reset` with it. An example that has become static also
    loses its stale interactive scene. Without a record of the previous build,
    every example is taken to have been interactive.

    Parameters
    ----------
    gallery_dir : Path
        The ``sphinx-gallery`` output directory.
    static : frozenset of str, optional
        The static examples. Defaults to :data:`STATIC`.

    Returns
    -------
    list of str
        The examples that were invalidated.

    """
    if static is None:
        static = STATIC

    state = gallery_dir / STATE

    try:
        previous = frozenset(json.loads(state.read_text(encoding="utf-8")))
    except (FileNotFoundError, ValueError):
        previous = frozenset()

    changed = sorted(previous ^ static)

    for name in changed:
        stem = name.rsplit(".", maxsplit=1)[-1]
        for checksum in gallery_dir.rglob(f"{stem}.py.md5"):
            checksum.unlink()
        if name in static:
            # the file name of another example may extend this one
            scene = re.compile(rf"sphx_glr_{re.escape(stem)}_\d+\.vtksz")
            for path in gallery_dir.rglob("*.vtksz"):
                if scene.fullmatch(path.name):
                    path.unlink()

    gallery_dir.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(sorted(static)), encoding="utf-8")

    return changed


def _builder_inited(app: Sphinx) -> None:
    """Invalidate changed examples before ``sphinx-gallery`` generates the gallery."""
    gallery_dirs = app.config.sphinx_gallery_conf["gallery_dirs"]

    if isinstance(gallery_dirs, str):
        gallery_dirs = [gallery_dirs]

    for gallery_dir in gallery_dirs:
        invalidate(Path(app.srcdir) / gallery_dir)


def setup(app: Sphinx) -> dict[str, bool]:
    """Configure the sphinx application.

    Parameters
    ----------
    app : Sphinx
        The sphinx application.

    Returns
    -------
    dict
        A dictionary declaring the extension safe for parallel reading and
        writing. It acts once, in the main process, before the gallery is
        generated.

    """
    # "sphinx_gallery.gen_gallery" generates the gallery at the default priority
    app.connect("builder-inited", _builder_inited, priority=400)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
