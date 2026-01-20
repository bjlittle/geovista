# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common.sanitize`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    import pyvista as pv

from geovista.common import _GV_SANITIZE, sanitize


def test_meshes_fail():
    """Test trap of no meshes."""
    emsg = "Expected one or more meshes"
    with pytest.raises(ValueError, match=emsg):
        sanitize()


@pytest.mark.parametrize("extra", [None, ["foo", "bar"], "baz"])
def test(lam_uk, extra):
    """Test removal of point and cell metadata."""

    def available(mesh: pv.PolyData) -> bool:
        return any(
            name in mesh.cell_data or name in mesh.point_data for name in cleanse
        )

    cleanse = _GV_SANITIZE.copy()

    if extra:
        if isinstance(extra, str):
            cleanse.append(extra)
        else:
            cleanse.extend(extra)

    nclean = len(cleanse)
    ncell, npoint = 1, 1

    assert not available(lam_uk)
    assert len(lam_uk.cell_data.keys()) == ncell
    assert len(lam_uk.point_data.keys()) == npoint

    for name in cleanse:
        lam_uk.cell_data[name] = np.arange(lam_uk.n_cells)
        lam_uk.point_data[name] = np.arange(lam_uk.n_points)

    assert len(lam_uk.cell_data.keys()) == nclean + ncell
    assert len(lam_uk.point_data.keys()) == nclean + npoint

    meshes = [lam_uk.copy() for _ in range(3)]

    for mesh in meshes:
        assert available(mesh)

    sanitize(*meshes, extra=extra)

    for mesh in meshes:
        assert not available(mesh)
        assert len(mesh.cell_data.keys()) == ncell
        assert len(mesh.point_data.keys()) == npoint
