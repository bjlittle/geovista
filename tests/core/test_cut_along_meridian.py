"""Unit-tests for :func:`geovista.core.cut_along_meridian`."""
import pytest
import pyvista as pv

from geovista.common import point_cloud
from geovista.core import cut_along_meridian


def test_mesh_fail():
    """Test trap of mesh instance type."""
    ugrid = pv.UniformGrid()
    emsg = f"Require a {str(pv.PolyData)!r} mesh"
    with pytest.raises(TypeError, match=emsg):
        _ = cut_along_meridian(ugrid)


def test_point_cloud_pass_thru(lam_uk):
    """Test point-cloud nop."""
    cloud = pv.PolyData(lam_uk.points)
    assert point_cloud(cloud)
    result = cut_along_meridian(cloud)
    assert result is cloud
    assert result == cloud
