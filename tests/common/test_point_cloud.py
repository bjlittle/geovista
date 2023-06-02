"""Unit-tests for :func:`geovista.common.point_cloud`."""
import pyvista as pv

from geovista.common import point_cloud
from geovista.geometry import coastlines


def test_point_cloud():
    """Detect mesh is a point-cloud."""
    mesh = pv.Plane()
    cloud = pv.PolyData(mesh.points)
    assert point_cloud(cloud)


def test_mesh():
    """Detect mesh is not a point-cloud."""
    mesh = pv.Plane()
    assert not point_cloud(mesh)


def test_lines():
    """Detect lines are not a point-cloud."""
    lines = coastlines()
    assert not point_cloud(lines)
