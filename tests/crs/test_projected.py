"""Unit-tests for :func:`geovista.crs.projected`."""
from pyproj import CRS
import pyvista as pv

from geovista.crs import WGS84, projected, to_wkt


def test_planar__no_crs():
    """Test that the mesh is projected."""
    mesh = pv.Plane()
    assert projected(mesh)


def test_planer__with_crs():
    """Test that the mesh CRS is used over the geometry heuristic."""
    mesh = pv.Plane()
    to_wkt(mesh, WGS84)
    assert not projected(mesh)


def test_non_planar__no_crs():
    """Test that the mesh is not projected."""
    mesh = pv.Sphere()
    assert not projected(mesh)


def test_non_planer__with_crs():
    """Test that the mesh CRS is used over the geometry heuristic."""
    mesh = pv.Sphere()
    crs = CRS.from_user_input("+proj=eqc")
    to_wkt(mesh, crs)
    assert projected(mesh)
