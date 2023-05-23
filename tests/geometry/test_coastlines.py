"""Unit-test for :func:`geovista.geometry.coastlines`."""
from geovista.common import COASTLINES_RESOLUTION
from geovista.geometry import coastlines


def test_defaults(mocker):
    """Test expected defaults are honoured."""
    mesh = mocker.sentinel.mesh
    fetch = mocker.patch("geovista.geometry.fetch_coastlines", return_value=mesh)
    resize = mocker.patch("geovista.geometry.resize")
    result = coastlines()
    assert result == mesh
    fetch.assert_called_once_with(resolution=COASTLINES_RESOLUTION)
    resize.assert_called_once_with(
        mesh, radius=None, zfactor=None, zlevel=1, inplace=True
    )


def test_resize_kwarg_pass_thru(mocker):
    """Test kwargs are passed thru to :func:`geovista.core.resize`."""
    mesh = mocker.sentinel.mesh
    resolution = mocker.sentinel.resolution
    radius = mocker.sentinel.radius
    zfactor = mocker.sentinel.zfactor
    zlevel = mocker.sentinel.zlevel
    fetch = mocker.patch("geovista.geometry.fetch_coastlines", return_value=mesh)
    resize = mocker.patch("geovista.geometry.resize")
    kwargs = {"radius": radius, "zfactor": zfactor, "zlevel": zlevel}
    result = coastlines(resolution=resolution, **kwargs)
    assert result == mesh
    fetch.assert_called_once_with(resolution=resolution)
    resize.assert_called_once_with(mesh, **kwargs, inplace=True)


def test_fetch_exception(mocker):
    """Test coastlines are loaded on cache fetch failure."""
    mesh = mocker.sentinel.mesh
    fetch = mocker.patch("geovista.geometry.fetch_coastlines", side_effect=ValueError)
    load = mocker.patch("geovista.geometry.load_coastlines", return_value=mesh)
    resize = mocker.patch("geovista.geometry.resize")
    result = coastlines()
    assert result == mesh
    assert fetch.call_count == 1
    assert resize.call_count == 1
    load.assert_called_once_with(resolution=COASTLINES_RESOLUTION)
