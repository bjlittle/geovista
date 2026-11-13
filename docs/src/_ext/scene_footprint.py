# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Shrink the interactive ``.vtksz`` scenes a build exports.

``pyvista`` exports each interactive scene through ``trame``, whose serializer
writes a texture as decoded RGB and every point as float64. A scene with the
base layer's 7,020 x 3,510 texture then carries 74 MB of raw pixels, about 39 MB
zipped, and the 47 scenes of a full build came to 1.7 GB, over the 1,024 MB that
Read the Docs allows for the HTML of a build (issue #2960).

Once the build has finished, :func:`build_finished` rewrites every scene under
the output: :func:`shrink` resamples a texture wider than :data:`MAX_WIDTH` to
that width, keeping its aspect, and stores float64 points as float32. A static
image keeps the full texture, since only the exported scene is rewritten.

Notes
-----
The texture resampling is a workaround for ``trame-vtk`` writing a texture as
raw RGB (Kitware/trame-vtk#128). Once it can write a compressed image, the
textures keep their full resolution, and only the points need rewriting: issue
#2963 retires the resampling.

.. versionadded:: 0.6.0

"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
import zipfile

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = ["MAX_WIDTH", "build_finished", "setup", "shrink"]

MAX_WIDTH: int = 2048
"""The widest texture, in pixels, that a scene keeps."""

#: The type code ``trame`` appends to an array's hash, by its numpy type.
_CODES = {np.dtype(np.uint8): "B", np.dtype(np.float32): "f"}


def _key(data: np.ndarray) -> str:
    """Return an array's hash, as ``trame`` writes it."""
    digest = hashlib.md5(data.tobytes(), usedforsecurity=False).hexdigest()
    return f"{digest}_{data.size}{_CODES[data.dtype]}"


def _store(hashes: dict[str, Any], data: np.ndarray, old: str, js_type: str) -> str:
    """Add an array to a scene's ``hashes`` in place of another; return its hash."""
    key = _key(data)
    entry = dict(hashes[old])
    entry.update(
        hash=key,
        type=js_type,
        content=base64.b64encode(data.tobytes()).decode("ascii"),
    )
    hashes[key] = entry
    return key


def _decoded(hashes: dict[str, Any], key: str, dtype: type) -> np.ndarray:
    """Decode an array of a scene by its hash."""
    content = hashes[key]["content"]
    return np.frombuffer(base64.b64decode(content), dtype=dtype)


def _texture(
    node: dict[str, Any], hashes: dict[str, Any], done: dict[str, str]
) -> bool:
    """Resample a texture's image wider than :data:`MAX_WIDTH`, in place."""
    props = node.get("properties", {})
    x0, x1, y0, y1, z0, z1 = props.get("extent", (0, 0, 0, 0, 0, 0))
    width, height = x1 - x0 + 1, y1 - y0 + 1
    if width <= MAX_WIDTH or z1 != z0:
        return False
    new_width = MAX_WIDTH
    new_height = max(1, round(height * new_width / width))
    changed = False
    for field in props.get("fields", []):
        components = field.get("numberOfComponents")
        if field.get("dataType") != "Uint8Array" or components not in (3, 4):
            continue
        old = field["hash"]
        if old not in done:
            pixels = _decoded(hashes, old, np.uint8).reshape(height, width, components)
            image = Image.fromarray(pixels)
            resized = np.asarray(
                image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            )
            done[old] = _store(hashes, np.ascontiguousarray(resized), old, "Uint8Array")
        field["hash"] = done[old]
        field["size"] = new_width * new_height * components
        field.pop("ranges", None)
        changed = True
    if changed:
        props["extent"] = [x0, x0 + new_width - 1, y0, y0 + new_height - 1, z0, z1]
    return changed


def _points(
    field: dict[str, Any], hashes: dict[str, Any], done: dict[str, str]
) -> bool:
    """Store a mesh's float64 points as float32, in place."""
    if field.get("dataType") != "Float64Array":
        return False
    old = field["hash"]
    if old not in done:
        values = _decoded(hashes, old, np.float64).astype(np.float32)
        done[old] = _store(hashes, values, old, "Float32Array")
    field["hash"] = done[old]
    field["dataType"] = "Float32Array"
    return True


def _nodes(item: object) -> list[dict[str, Any]]:
    """Return every node of a scene, depth first."""
    found: list[dict[str, Any]] = []
    stack = [item]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            found.append(current)
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


def shrink(path: Path) -> tuple[int, int]:
    """Rewrite a ``.vtksz`` scene in place, with smaller textures and points.

    Parameters
    ----------
    path : Path
        The scene.

    Returns
    -------
    tuple of int
        The scene's size in bytes, before and after.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    before = path.stat().st_size
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    index = json.loads(members["index.json"])
    hashes = index.get("hashes", {})
    done: dict[str, str] = {}
    changed = False
    for node in _nodes(index.get("scene", {})):
        if node.get("type") == "vtkImageData":
            changed |= _texture(node, hashes, done)
        points = (
            node.get("properties", {}).get("points")
            if isinstance(node.get("properties"), dict)
            else None
        )
        if isinstance(points, dict):
            changed |= _points(points, hashes, done)
    if not changed:
        return before, before
    # trame shares an array between fields with the same contents, so a replaced
    # array may still be another field's, such as normals equal to the points.
    referenced = {
        node["hash"]
        for node in _nodes(index.get("scene", {}))
        if isinstance(node.get("hash"), str)
    }
    for old in done:
        if old not in referenced:
            hashes.pop(old, None)
    members["index.json"] = json.dumps(index).encode("utf-8")
    partial = path.with_suffix(".vtksz.partial")
    with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    partial.replace(path)
    return before, path.stat().st_size


def build_finished(app: Sphinx, exception: Exception | None) -> None:
    """Shrink every scene the build wrote, once it has finished.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application.
    exception : Exception, optional
        The exception that ended the build, if any.

    Notes
    -----
    Only the build's own log needs ``sphinx``, which is imported here, so that
    :func:`shrink` runs in an environment without it, as the tests do.

    .. versionadded:: 0.6.0

    """
    if exception is not None or app.builder.format != "html":
        return
    total_before = total_after = count = 0
    for path in sorted(Path(app.outdir).rglob("*.vtksz")):
        before, after = shrink(path)
        total_before += before
        total_after += after
        count += 1
    if count:
        from sphinx.util import logging  # noqa: PLC0415

        logging.getLogger(__name__).info(
            "scene_footprint: %d scenes, %.0f MB -> %.0f MB",
            count,
            total_before / 1e6,
            total_after / 1e6,
        )


def setup(app: Sphinx) -> dict[str, Any]:
    """Shrink the exported scenes once the build has finished.

    Parameters
    ----------
    app : Sphinx
        The Sphinx application.

    Returns
    -------
    dict
        The extension's metadata.

    Notes
    -----
    .. versionadded:: 0.6.0

    """
    app.connect("build-finished", build_finished)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
