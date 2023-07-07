"""Unit-tests for :func:`geovista.core.slice_cells`."""
from __future__ import annotations

import pytest
import pyvista as pv

from geovista.common import point_cloud
from geovista.core import slice_cells

try:
    from pyvista import ImageData
except ImportError:
    from pyvista import UniformGrid as ImageData


def test_mesh_fail():
    """Test trap of mesh instance type."""
    ugrid = ImageData()
    emsg = f"Require a {str(pv.PolyData)!r} mesh"
    with pytest.raises(TypeError, match=emsg):
        _ = slice_cells(ugrid)


def test_point_cloud_pass_thru(lam_uk):
    """Test point-cloud nop."""
    cloud = pv.PolyData(lam_uk.points)
    assert point_cloud(cloud)
    result = slice_cells(cloud)
    assert result is cloud
    assert result == cloud
