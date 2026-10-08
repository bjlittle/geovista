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


@pytest.fixture
def gallery(tmp_path: Path) -> Path:
    """Provide gallery output holding two cached examples and their scenes."""
    root = tmp_path / "gallery"
    for folder, stem in [("grid", "reykjanes"), ("grid", "reykjanes_contour")]:
        images = root / folder / "images"
        images.mkdir(parents=True, exist_ok=True)
        (root / folder / f"{stem}.py.md5").write_text("cached")
        (images / f"sphx_glr_{stem}_001.vtksz").write_text("scene")
    return root


def _cached(gallery: Path, stem: str) -> bool:
    return (gallery / "grid" / f"{stem}.py.md5").exists()


def _scene(gallery: Path, stem: str) -> bool:
    return (gallery / "grid" / "images" / f"sphx_glr_{stem}_001.vtksz").exists()


def test_invalidate_to_static(scenes, gallery):
    """Test an example newly made static is rebuilt without its stale scene.

    With no record of the previous build, every example is taken to have been
    interactive, as was every build before the static scenes.

    """
    changed = scenes.invalidate(gallery, frozenset({"grid.reykjanes"}))
    assert changed == ["grid.reykjanes"]
    assert not _cached(gallery, "reykjanes")
    assert not _scene(gallery, "reykjanes")
    # a file name that shares the prefix is a different example
    assert _cached(gallery, "reykjanes_contour")
    assert _scene(gallery, "reykjanes_contour")


def test_invalidate_to_interactive(scenes, gallery):
    """Test an example no longer static is rebuilt to regain its scene."""
    scenes.invalidate(gallery, frozenset({"grid.reykjanes"}))
    (gallery / "grid" / "reykjanes.py.md5").write_text("cached")
    changed = scenes.invalidate(gallery, frozenset())
    assert changed == ["grid.reykjanes"]
    assert not _cached(gallery, "reykjanes")


def test_invalidate_unchanged(scenes, gallery):
    """Test the cache is kept when the static examples have not changed."""
    scenes.invalidate(gallery, frozenset({"grid.reykjanes"}))
    (gallery / "grid" / "reykjanes.py.md5").write_text("cached")
    assert scenes.invalidate(gallery, frozenset({"grid.reykjanes"})) == []
    assert _cached(gallery, "reykjanes")


EXAMPLE = '''"""
Reykjanes
=========

Report whether the scene export component is registered.
"""

import pyvista as pv

names = {item.name for item in pv.registered_plotter_components()}
print("COMPONENT_PRESENT", "trame" in names)
'''


@pytest.mark.usefixtures("scenes")
def test_incremental_build(tmp_path, monkeypatch, require):
    """Test changing the static examples applies to an incremental build.

    sphinx-gallery skips an example whose source is unchanged, so without the
    invalidation the reset hook never runs for it and its output goes stale.

    """
    try:
        from sphinx.application import Sphinx  # noqa: PLC0415
    except ImportError:
        require("sphinx is not installed")

    src = tmp_path / "src"
    (src / "examples").mkdir(parents=True)
    (src / "examples" / "GALLERY_HEADER.rst").write_text("Gallery\n=======\n")
    (src / "examples" / "reykjanes.py").write_text(EXAMPLE)
    (src / "index.rst").write_text("Test\n====\n\n.. toctree::\n\n   gallery/index\n")
    (src / "conf.py").write_text(
        "extensions = ['sphinx_gallery.gen_gallery', 'gallery_scenes']\n"
        "sphinx_gallery_conf = {\n"
        "    'examples_dirs': 'examples',\n"
        "    'filename_pattern': '/.*',\n"
        "    'gallery_dirs': 'gallery',\n"
        "    'reset_modules': ('gallery_scenes.reset',),\n"
        "    'reset_modules_order': 'both',\n"
        "}\n"
    )
    # the build imports the extension by bare name, so patch that module
    monkeypatch.syspath_prepend(str(EXT))
    import gallery_scenes  # noqa: PLC0415

    def build(static: frozenset[str]) -> bool:
        monkeypatch.setattr(gallery_scenes, "STATIC", static)
        app = Sphinx(
            str(src),
            str(src),
            str(tmp_path / "html"),
            str(tmp_path / "doctrees"),
            "html",
            status=None,
            warning=None,
        )
        app.build()
        text = (src / "gallery" / "reykjanes.rst").read_text()
        return "COMPONENT_PRESENT True" in text

    assert build(frozenset()) is True
    assert build(frozenset({"grid.reykjanes"})) is False
    assert build(frozenset()) is True
