# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Guards that every radius became a globe (scene spec §4.2 and scene spec §4.3)."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import numpy as np
import pytest

import geovista
from geovista.bridge import Transform
from geovista.common import get_modules, to_cartesian
from geovista.core import resize
from geovista.crs import WGS84
from geovista.geodesic import BBox, line
from geovista.geometry import coastlines
from geovista.globe import Globe
from geovista.gridlines import create_meridians, create_parallels
from geovista.pantry.meshes import regular_grid
from geovista.transform import transform_mesh

#: The package source, whose modules the guards read.
PACKAGE = Path(geovista.__file__).parent

#: The private functions of scene spec §3.1 that took a radius.
PRIVATE = [
    ("geoplotter", "_lfric_mesh"),
    ("geoplotter", "GeoPlotterBase._add_graticule_labels"),
    ("geodesic", "BBox._generate_bbox_mesh"),
    ("transform", "_record_zlevels"),
]

#: The public functions of scene spec §3.1 that took a radius, but the methods of
#: GeoPlotter, which take the globe of their scene, and the plotter that takes it.
SIZED = [
    ("bridge", "Transform.__init__"),
    ("bridge", "Transform.from_1d"),
    ("bridge", "Transform.from_2d"),
    ("bridge", "Transform.from_points"),
    ("bridge", "Transform.from_tiff"),
    ("bridge", "Transform.from_unstructured"),
    ("bridge", "Transform.to_structured_grid"),
    ("common", "to_cartesian"),
    ("common", "vectors_to_cartesian"),
    ("common", "to_lonlat"),
    ("common", "to_lonlats"),
    ("core", "resize"),
    ("geodesic", "line"),
    ("geodesic", "BBox.boundary"),
    ("geometry", "coastlines"),
    ("geometry", "load_coastlines"),
    ("geoplotter", "GeoPlotterBase.__init__"),
    ("gridlines", "create_meridians"),
    ("gridlines", "create_parallels"),
    ("pantry.meshes", "regular_grid"),
    ("search", "KDTree.query"),
    ("transform", "transform_mesh"),
]

#: The globe each builder below is given, at twice the default render radius.
GLOBE = Globe(render_radius=2)

#: A mesh each builder of scene spec §3.1 makes on the globe it is given.
BUILT = {
    "Transform": lambda globe: Transform([0.0, 10.0], [0.0, 10.0], globe=globe)(),
    "from_1d": lambda globe: Transform.from_1d(
        [0.0, 10.0, 20.0], [0.0, 10.0], globe=globe
    ),
    "from_2d": lambda globe: Transform.from_2d(
        *np.meshgrid([0.0, 10.0, 20.0], [0.0, 10.0]), globe=globe
    ),
    "from_points": lambda globe: Transform.from_points(
        [0.0, 10.0], [0.0, 10.0], globe=globe
    ),
    "line": lambda globe: line([0, 10], [0, 10], globe=globe),
    "boundary": lambda globe: BBox([0, 10, 10, 0], [0, 0, 10, 10]).boundary(
        globe=globe
    ),
    "coastlines": lambda globe: coastlines(resolution="110m", globe=globe),
    "meridians": lambda globe: create_meridians(globe=globe).blocks[0],
    "parallels": lambda globe: create_parallels(globe=globe).blocks[0],
    "regular_grid": lambda globe: regular_grid(globe=globe),
    "resize": lambda globe: resize(
        Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0]), globe=globe
    ),
    "transform_mesh": lambda globe: transform_mesh(
        transform_mesh(Transform.from_1d([0.0, 10.0, 20.0], [0.0, 10.0]), "+proj=eqc"),
        WGS84,
        globe=globe,
    ),
}


def _callables(module: object) -> list[tuple[str, object]]:
    """Return each public function and method a module defines, by name."""
    found = []
    for name, value in vars(module).items():
        if name.startswith("_") or getattr(value, "__module__", None) != getattr(
            module, "__name__", None
        ):
            continue
        if inspect.isclass(value):
            for attr, member in vars(value).items():
                if (not attr.startswith("_") or attr in ("__init__", "__call__")) and (
                    inspect.isfunction(member) or isinstance(member, classmethod)
                ):
                    found.append((f"{name}.{attr}", member))
        elif callable(value):
            found.append((name, value))
    return found


def _parameters(function: object) -> list[str]:
    """Return the parameter names of a function, or none for a builtin."""
    if isinstance(function, classmethod):
        function = function.__func__
    try:
        return list(inspect.signature(function).parameters)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return []


def test_no_function_takes_a_radius():
    """Test no public function or method of geovista takes a radius, but the globe.

    Holds scene spec §2 decision 1, scene spec §2 decision 2.
    """
    offenders = []
    for name in get_modules("geovista"):
        if name == "__main__":
            continue
        try:
            module = importlib.import_module(f"geovista.{name}")
        except ModuleNotFoundError as error:
            # an optional dependency, such as pyvistaqt for geovista.qt
            if error.name and not error.name.startswith("geovista"):
                continue
            raise
        offenders.extend(
            f"geovista.{name}.{qualname}"
            for qualname, function in _callables(module)
            if "radius" in _parameters(function)
        )
    assert offenders == ["geovista.globe.Globe.__init__"]


@pytest.mark.parametrize(("module", "qualname"), SIZED)
def test_every_function_that_sizes_a_sphere_takes_a_globe(module, qualname):
    """Test each function of the census takes a globe, by keyword and none by default.

    Holds scene spec §2 decision 1.
    """
    value: object = importlib.import_module(f"geovista.{module}")
    for part in qualname.split("."):
        value = getattr(value, part)
    if isinstance(value, classmethod):
        value = value.__func__
    parameter = inspect.signature(value).parameters.get("globe")  # type: ignore[arg-type]
    assert parameter is not None
    assert parameter.kind in (parameter.KEYWORD_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    assert parameter.default is None


@pytest.mark.parametrize("build", BUILT.values(), ids=BUILT.keys())
def test_every_builder_uses_the_globe_given(build):
    """Test each builder of the census makes its mesh on the globe it is given.

    The mesh records the globe, and its points, lifts included, lie at twice those
    built on the default globe, as the render radius is twice the default.

    Holds scene spec §2 decision 1.
    """
    mesh = build(GLOBE)
    assert Globe.from_mesh(mesh) == GLOBE
    np.testing.assert_allclose(mesh.points, 2 * build(Globe()).points)


def test_cartesian_points_lie_on_the_globe_given():
    """Test points converted to cartesian lie at the render radius of the globe given.

    Holds scene spec §2 decision 1.
    """
    xyz = to_cartesian([0, 10, 20], [0, 10, -10], globe=GLOBE)
    np.testing.assert_allclose(np.linalg.norm(xyz, axis=-1), GLOBE.render_radius)


@pytest.mark.parametrize(("module", "qualname"), PRIVATE)
def test_no_private_function_of_the_census_takes_a_radius(module, qualname):
    """Test the private functions that took a radius take none."""
    value: object = importlib.import_module(f"geovista.{module}")
    for part in qualname.split("."):
        value = getattr(value, part)
    assert "radius" not in _parameters(value)


def test_only_the_globe_reads_gvradius():
    """Test only common, which retires it, and globe, which reads it, name gvRadius."""
    naming = set()
    for path in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            named = (isinstance(node, ast.Name) and node.id == "GV_FIELD_RADIUS") or (
                isinstance(node, ast.alias) and node.name == "GV_FIELD_RADIUS"
            )
            if named:
                naming.add(path.relative_to(PACKAGE).as_posix())
    assert naming == {"common.py", "globe.py"}
