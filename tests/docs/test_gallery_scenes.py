# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for the static ``sphinx-gallery`` scenes in ``docs/src/_ext``."""

from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType
    from typing import NoReturn

try:
    import pyvista as pv
    import trame_pyvista
except ImportError:
    pv = trame_pyvista = None

from geovista.common import get_modules

EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"

EXAMPLES = Path(__file__).parents[2] / "src" / "geovista" / "examples"

COMPONENT = "trame"


def _registered() -> bool:
    """Determine whether the ``trame`` plotter component is registered."""
    return COMPONENT in {item.name for item in pv.registered_plotter_components()}


@pytest.fixture
def scenes(require: Callable[[str], NoReturn], monkeypatch) -> ModuleType:
    """Load the module, restoring the ``trame`` plotter component afterwards."""
    if trame_pyvista is None:
        require("pyvista and trame-pyvista are not installed")

    path = EXT / "gallery_scenes.py"
    spec = importlib.util.spec_from_file_location("gallery_scenes_under_test", path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    assert _registered()
    yield module
    # never leak an unregistered component into other tests
    module.reset({}, "", "after")
    assert _registered()


def test_static_unique_stems():
    """Test each example file name is unique, as the hook is only given that."""
    stems = Counter(path.stem for path in EXAMPLES.rglob("*.py"))
    stems.pop("__init__", None)
    assert [stem for stem, count in stems.items() if count > 1] == []


def test_static_examples_exist(scenes):
    """Test each static example names a real example, so none goes stale."""
    assert scenes.STATIC - set(get_modules("geovista.examples")) == set()


@pytest.mark.parametrize("example", ["grid.reykjanes_contour", "spatial_index.uber_h3"])
def test_static(scenes, example):
    """Test a static example is run without the scene export component."""
    assert example in scenes.STATIC
    scenes.reset({}, f"{example.split('.')[-1]}.py", "before")
    assert not _registered()
    scenes.reset({}, f"{example.split('.')[-1]}.py", "after")
    assert _registered()


def test_interactive(scenes):
    """Test an interactive example keeps the scene export component."""
    assert "unstructured.icon" not in scenes.STATIC
    scenes.reset({}, "icon.py", "before")
    assert _registered()
    scenes.reset({}, "icon.py", "after")
    assert _registered()


def test_interactive_after_static(scenes):
    """Test an interactive example after a static one regains the component.

    A parallel worker runs many examples, and nothing guarantees an "after"
    call reaches it between them, so "before" must set the state outright.

    """
    scenes.reset({}, "reykjanes.py", "before")
    assert not _registered()
    scenes.reset({}, "icon.py", "before")
    assert _registered()


def test_unknown(scenes):
    """Test a file that is not a gallery example leaves the component alone."""
    scenes.reset({}, "not_an_example.py", "before")
    assert _registered()


@pytest.mark.parametrize(
    ("fname", "exported"), [("reykjanes.py", False), ("icon.py", True)]
)
def test_show(scenes, monkeypatch, fname, exported):
    """Test ``show`` exports a scene in a gallery build only when interactive."""
    monkeypatch.setattr(pv, "BUILDING_GALLERY", True)
    scenes.reset({}, fname, "before")
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(pv.Sphere())
    plotter.show()
    try:
        assert plotter.last_image is not None
        assert (plotter.last_vtksz is not None) is exported
    finally:
        pv.close_all()
        scenes.reset({}, fname, "after")
