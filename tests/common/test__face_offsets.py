# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

"""Unit-tests for :func:`geovista.common._face_offsets`."""

from __future__ import annotations

import numpy as np
import pyvista as pv

from geovista.common import _face_offsets as face_offsets


def test_no_faces():
    """Test offsets of a mesh with no faces."""
    mesh = pv.PolyData(np.random.default_rng().random((4, 3)))
    np.testing.assert_array_equal(face_offsets(mesh), [0])


def test_regular_faces():
    """Test offsets of a mesh with faces of a common size."""
    points = np.random.default_rng().random((6, 3))
    mesh = pv.PolyData.from_regular_faces(points, [[0, 1, 2], [3, 4, 5]])
    np.testing.assert_array_equal(face_offsets(mesh), [0, 3, 6])


def test_irregular_faces():
    """Test offsets of a mesh with faces of differing sizes."""
    points = np.random.default_rng().random((8, 3))
    mesh = pv.PolyData(points, faces=[3, 0, 1, 2, 4, 3, 4, 5, 6])
    np.testing.assert_array_equal(face_offsets(mesh), [0, 3, 7])


def test_lam(lam_uk):
    """Test offsets of a quad-cell mesh."""
    expected = 4 * np.arange(lam_uk.n_faces + 1)
    np.testing.assert_array_equal(face_offsets(lam_uk), expected)
