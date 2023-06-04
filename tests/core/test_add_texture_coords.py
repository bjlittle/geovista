"""Unit-tests for :func:`geovista.core.add_texture_coords`."""
import pyvista as pv

from geovista.common import point_cloud
from geovista.core import add_texture_coords


def test_point_cloud_pass_thru(lam_uk):
    """Test point-cloud nop."""
    cloud = pv.PolyData(lam_uk.points)
    assert point_cloud(cloud)
    result = add_texture_coords(cloud)
    assert result is cloud
    assert result == cloud
