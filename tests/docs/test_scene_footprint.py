# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for shrinking the exported ``.vtksz`` scenes in ``docs/src/_ext``."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any
import zipfile

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType
    from typing import NoReturn

EXT = Path(__file__).parents[2] / "docs" / "src" / "_ext"

#: The type code trame appends to an array's hash, by its numpy type.
CODES = {np.dtype(np.uint8): "B", np.dtype(np.float32): "f", np.dtype(np.float64): "d"}

#: The vtk.js array type, by numpy type.
TYPES = {
    np.dtype(np.uint8): "Uint8Array",
    np.dtype(np.float32): "Float32Array",
    np.dtype(np.float64): "Float64Array",
}


@pytest.fixture
def footprint(monkeypatch) -> ModuleType:
    """Load the extension under test."""
    path = EXT / "scene_footprint.py"
    spec = importlib.util.spec_from_file_location("scene_footprint_under_test", path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


def _array(values: np.ndarray, vtk: str) -> tuple[str, dict[str, Any]]:
    """Return an array's hash and its entry in a scene's ``hashes``, as trame writes."""
    data = np.ascontiguousarray(values)
    key = f"{hashlib.md5(data.tobytes()).hexdigest()}_{data.size}{CODES[data.dtype]}"  # noqa: S324
    entry = {
        "hash": key,
        "type": TYPES[data.dtype],
        "vtk": vtk,
        "content": base64.b64encode(data.tobytes()).decode("ascii"),
    }
    return key, entry


def _image_node(key: str, width: int, height: int, components: int) -> dict[str, Any]:
    """Return a texture's ``vtkImageData`` node, as trame writes it."""
    return {
        "parent": "texture",
        "id": "texture-image",
        "type": "vtkImageData",
        "properties": {
            "spacing": [1.0, 1.0, 1.0],
            "origin": [0.0, 0.0, 0.0],
            "extent": [0, width - 1, 0, height - 1, 0, 0],
            "fields": [
                {
                    "hash": key,
                    "vtkClass": "vtkDataArray",
                    "name": "JPEGImage",
                    "dataType": "Uint8Array",
                    "numberOfComponents": components,
                    "size": width * height * components,
                    "location": "pointData",
                    "registration": "setScalars",
                }
            ],
        },
    }


def _mesh_node(key: str, size: int, dtype: str) -> dict[str, Any]:
    """Return a ``vtkPolyData`` node, as trame writes it."""
    return {
        "parent": "mapper",
        "id": "mesh",
        "type": "vtkPolyData",
        "properties": {
            "points": {
                "hash": key,
                "vtkClass": "vtkPoints",
                "name": "Points",
                "dataType": dtype,
                "numberOfComponents": 3,
                "size": size,
            },
        },
    }


def _scene(
    path: Path,
    *,
    width: int = 4096,
    height: int = 2048,
    components: int = 3,
    textures: int = 1,
    points: np.ndarray | None = None,
) -> Path:
    """Write a small ``.vtksz`` holding a texture and a mesh, as trame does."""
    rng = np.random.default_rng(0)
    image = rng.integers(0, 256, size=(height, width, components), dtype=np.uint8)
    image_key, image_entry = _array(image, "vtkImageData")
    if points is None:
        points = rng.random((10, 3))
    points_key, points_entry = _array(points, "vtkPoints")
    nodes = [_image_node(image_key, width, height, components) for _ in range(textures)]
    nodes.append(_mesh_node(points_key, points.size, TYPES[points.dtype]))
    index = {
        "scene": {"type": "vtkRenderWindow", "dependencies": nodes},
        "hashes": {image_key: image_entry, points_key: points_entry},
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("index.json", json.dumps(index))
    return path


def _read(path: Path) -> dict[str, Any]:
    """Read a scene's ``index.json``."""
    with zipfile.ZipFile(path) as archive:
        result: dict[str, Any] = json.loads(archive.read("index.json"))
    return result


def _nodes(index: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    """Return every node of a type in a scene."""
    found = []

    def walk(item: object) -> None:
        if isinstance(item, dict):
            if item.get("type") == kind:
                found.append(item)
            for value in item.values():
                walk(value)
        elif isinstance(item, list):
            for value in item:
                walk(value)

    walk(index["scene"])
    return found


def _decoded(index: dict[str, Any], key: str, dtype: type) -> np.ndarray:
    """Decode an array of a scene by its hash."""
    content = index["hashes"][key]["content"]
    return np.frombuffer(base64.b64decode(content), dtype=dtype)


def test_a_wide_texture_is_resampled(footprint, tmp_path):
    """A texture wider than the limit is resampled to it, keeping its aspect."""
    path = _scene(tmp_path / "scene.vtksz", width=4096, height=2048)
    footprint.shrink(path)
    index = _read(path)
    (image,) = _nodes(index, "vtkImageData")
    width = footprint.MAX_WIDTH
    assert image["properties"]["extent"] == [0, width - 1, 0, width // 2 - 1, 0, 0]
    (field,) = image["properties"]["fields"]
    assert field["size"] == width * (width // 2) * 3
    pixels = _decoded(index, field["hash"], np.uint8)
    assert pixels.size == field["size"]
    digest, count = field["hash"].split("_")
    assert digest == hashlib.md5(pixels.tobytes()).hexdigest()  # noqa: S324
    assert count == f"{pixels.size}B"
    assert index["hashes"][field["hash"]]["type"] == "Uint8Array"


def test_the_old_texture_is_dropped(footprint, tmp_path):
    """The full-resolution texture leaves the scene once nothing refers to it."""
    path = _scene(tmp_path / "scene.vtksz")
    (old,) = _nodes(_read(path), "vtkImageData")
    old_key = old["properties"]["fields"][0]["hash"]
    footprint.shrink(path)
    index = _read(path)
    (image,) = _nodes(index, "vtkImageData")
    kept = {image["properties"]["fields"][0]["hash"]}
    kept |= {
        node["properties"]["points"]["hash"] for node in _nodes(index, "vtkPolyData")
    }
    assert set(index["hashes"]) == kept
    assert old_key not in index["hashes"]


def test_a_shared_texture_is_resampled_once(footprint, tmp_path):
    """Two textures sharing one image both point at its one resampled copy."""
    path = _scene(tmp_path / "scene.vtksz", textures=2)
    footprint.shrink(path)
    index = _read(path)
    keys = {
        node["properties"]["fields"][0]["hash"]
        for node in _nodes(index, "vtkImageData")
    }
    assert len(keys) == 1
    assert next(iter(keys)) in index["hashes"]


def test_rgba_keeps_its_alpha(footprint, tmp_path):
    """A texture with an alpha channel keeps four components."""
    path = _scene(tmp_path / "scene.vtksz", width=3000, height=1000, components=4)
    footprint.shrink(path)
    (image,) = _nodes(_read(path), "vtkImageData")
    field = image["properties"]["fields"][0]
    assert field["numberOfComponents"] == 4
    assert (
        field["size"]
        == footprint.MAX_WIDTH * round(1000 * footprint.MAX_WIDTH / 3000) * 4
    )


def test_a_narrow_texture_is_kept(footprint, tmp_path):
    """A texture no wider than the limit is left as it is."""
    path = _scene(tmp_path / "scene.vtksz", width=1024, height=512)
    before = _read(path)
    footprint.shrink(path)
    after = _read(path)
    (old,), (new,) = _nodes(before, "vtkImageData"), _nodes(after, "vtkImageData")
    assert old == new


def test_points_are_stored_as_float32(footprint, tmp_path):
    """Float64 points are stored as float32, with the same values to its precision."""
    points = np.random.default_rng(1).random((100, 3)) * 6378137.0
    path = _scene(tmp_path / "scene.vtksz", points=points)
    footprint.shrink(path)
    index = _read(path)
    (mesh,) = _nodes(index, "vtkPolyData")
    field = mesh["properties"]["points"]
    assert field["dataType"] == "Float32Array"
    assert field["size"] == points.size
    assert field["hash"].endswith(f"_{points.size}f")
    assert index["hashes"][field["hash"]]["type"] == "Float32Array"
    stored = _decoded(index, field["hash"], np.float32).reshape(-1, 3)
    np.testing.assert_allclose(stored, points, rtol=1e-6)


def test_float32_points_are_kept(footprint, tmp_path):
    """Points already in float32 are left as they are."""
    points = np.random.default_rng(2).random((10, 3)).astype(np.float32)
    path = _scene(tmp_path / "scene.vtksz", width=64, height=32, points=points)
    before = path.read_bytes()
    footprint.shrink(path)
    assert path.read_bytes() == before


def test_a_second_run_changes_nothing(footprint, tmp_path):
    """Shrinking a scene twice leaves it as the first run did."""
    path = _scene(tmp_path / "scene.vtksz")
    footprint.shrink(path)
    once = path.read_bytes()
    footprint.shrink(path)
    assert path.read_bytes() == once


def test_shrink_reports_the_sizes(footprint, tmp_path):
    """Shrinking returns the scene's size before and after."""
    path = _scene(tmp_path / "scene.vtksz")
    before = path.stat().st_size
    result = footprint.shrink(path)
    assert result == (before, path.stat().st_size)
    assert result[1] < result[0]


def test_setup_connects_build_finished_and_is_parallel_safe(footprint, mocker):
    """The extension shrinks the scenes once the build has written them."""
    app = mocker.MagicMock()
    meta = footprint.setup(app)
    app.connect.assert_called_once_with("build-finished", footprint.build_finished)
    assert meta["parallel_read_safe"] is True
    assert meta["parallel_write_safe"] is True


def test_build_finished_shrinks_every_scene(footprint, tmp_path, mocker):
    """Every scene under the output, at any depth, is shrunk."""
    nested = tmp_path / "_images" / "generated" / "gallery"
    nested.mkdir(parents=True)
    paths = [_scene(tmp_path / "_images" / "a.vtksz"), _scene(nested / "b.vtksz")]
    app = mocker.MagicMock(outdir=str(tmp_path))
    app.builder.format = "html"
    footprint.build_finished(app, None)
    for path in paths:
        (image,) = _nodes(_read(path), "vtkImageData")
        assert image["properties"]["extent"][1] == footprint.MAX_WIDTH - 1


def test_build_finished_skips_a_failed_build(footprint, tmp_path, mocker):
    """A build that raised leaves its scenes alone."""
    path = _scene(tmp_path / "a.vtksz")
    before = path.read_bytes()
    app = mocker.MagicMock(outdir=str(tmp_path))
    app.builder.format = "html"
    footprint.build_finished(app, RuntimeError("boom"))
    assert path.read_bytes() == before


@pytest.mark.image
def test_a_scene_pyvista_exports(
    footprint, tmp_path, require: Callable[[str], NoReturn]
):
    """A scene exported by ``pyvista`` through trame is shrunk as the others are."""
    try:
        import pyvista as pv  # noqa: PLC0415
        import trame_pyvista  # noqa: F401, PLC0415
    except ImportError:
        require("pyvista and trame-pyvista are not installed")
    image = np.random.default_rng(3).integers(
        0, 256, size=(1500, 3000, 3), dtype=np.uint8
    )
    p = pv.Plotter(off_screen=True)
    p.add_mesh(pv.Sphere().texture_map_to_sphere(), texture=pv.Texture(image))
    path = tmp_path / "scene.vtksz"
    p.trame.export_vtksz(filename=str(path))
    p.close()
    before, after = footprint.shrink(path)
    assert after < before
    index = _read(path)
    (node,) = _nodes(index, "vtkImageData")
    assert node["properties"]["extent"][1] == footprint.MAX_WIDTH - 1
    for mesh in _nodes(index, "vtkPolyData"):
        assert mesh["properties"]["points"]["dataType"] == "Float32Array"
