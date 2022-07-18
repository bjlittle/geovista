"""
This module contains convenience functions to download, cache and load
geovista sample data, which can then be used by the :mod:`geovista.bridge`
to generate a mesh.

"""

from dataclasses import dataclass, field
from typing import Optional

import netCDF4 as nc
import numpy as np
import numpy.typing as npt
import pooch

from .cache import CACHE

__all__ = ["hexahedron", "orca2", "ww3_global_smc", "ww3_global_tri"]


@dataclass(frozen=True)
class SampleStructuredXY:
    lons: npt.ArrayLike
    lats: npt.ArrayLike
    data: npt.ArrayLike
    name: str = field(default=None)
    units: str = field(default=None)
    steps: int = field(default=None)
    ndim: int = 2


@dataclass(frozen=True)
class SampleUnstructuredXY:
    lons: npt.ArrayLike
    lats: npt.ArrayLike
    connectivity: npt.ArrayLike
    data: npt.ArrayLike
    name: str = field(default=None)
    units: str = field(default=None)
    steps: int = field(default=None)
    ndim: int = 2


def capitalise(title: str) -> str:
    """
    Format the title by capitalising each word and replacing
    inappropriate characters.

    Returns
    -------
    str

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    title = title.replace("_", " ")
    title = title.split(" ")
    title = " ".join([word.capitalize() for word in title])

    return title


def fesom(step: Optional[int] = None) -> SampleUnstructuredXY:
    """
    Load AWI-CM FESOM 1.4 unstructured mesh.

    Parameters
    ----------
    step : int
        Timeseries index offset.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "tos_Omon_AWI-ESM-1-1-LR_historical_r1i1p1f1_gn_185001-185012.nc"
    resource = CACHE.fetch(f"{fname}")
    ds = nc.Dataset(resource)

    # load the lon/lat cell grid
    lons = ds.variables["lon_bnds"][:]
    lats = ds.variables["lat_bnds"][:]

    # load the mesh payload
    data = ds.variables["tos"]
    name = capitalise(data.standard_name)
    units = data.units

    # deal with the timeseries step
    steps = ds.dimensions["time"].size
    idx = 0 if step is None else (step % steps)

    sample = SampleUnstructuredXY(lons, lats, lons.shape, data[idx], name, units, steps)

    return sample


def hexahedron() -> SampleUnstructuredXY:
    """
    Load DYNAMICO hexahedron unstructured mesh.

    Returns
    -------
    SampleUnstructuredXY
        The hexagonal unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "hexahedron.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"samples/{fname}.bz2", processor=processor)
    ds = nc.Dataset(resource)

    # load the lon/lat hex cell grid
    lons = ds.variables["bounds_lon_i"][:]
    lats = ds.variables["bounds_lat_i"][:]

    # load the mesh payload
    data = ds.variables["phis"][:]
    name = capitalise("synthetic")
    units = 1

    sample = SampleUnstructuredXY(lons, lats, lons.shape, data, name, units)

    return sample


def orca2() -> SampleStructuredXY:
    """
    Load ORCA2 curvilinear mesh.

    Returns
    -------
    SampleStructuredXY
        The curvilinear spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "votemper.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"samples/{fname}.bz2", processor=processor)
    ds = nc.Dataset(resource)

    # load the lon/lat grid
    lons = ds.variables["lont_bounds"][:]
    lats = ds.variables["latt_bounds"][:]

    # load the mesh payload
    data = ds.variables["votemper"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleStructuredXY(lons, lats, data[0, 0], name, units)

    return sample


def ww3_global_smc(step: Optional[int] = None) -> SampleUnstructuredXY:
    """
    Load the WAVEWATCH III (WW3) unstructured Spherical Multi-Cell (SMC) mesh.

    Parameters
    ----------
    step : int
        Timeseries index offset.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "ww3_gbl_smc_hs.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"samples/ww3/{fname}.bz2", processor=processor)
    ds = nc.Dataset(resource)

    # load the lon/lat grid cell centres
    cc_lons = ds.variables["longitude"][:]
    cc_lats = ds.variables["latitude"][:]

    # load integer scaling factor for the grid cells
    cx = ds.variables["cx"][:]
    cy = ds.variables["cy"][:]
    base_lon_size = ds.getncattr("base_lon_size")
    base_lat_size = ds.getncattr("base_lat_size")

    # construct the grid cells
    dlon = cx * base_lon_size
    dlat = cy * base_lat_size
    fac = 0.5
    x1 = (cc_lons - fac * dlon).reshape(-1, 1)
    x2 = (cc_lons + fac * dlon).reshape(-1, 1)
    y1 = (cc_lats - fac * dlat).reshape(-1, 1)
    y2 = (cc_lats + fac * dlat).reshape(-1, 1)

    lons = np.hstack([x1, x2, x2, x1])
    lats = np.hstack([y1, y1, y2, y2])

    # deal with the timeseries step
    steps = ds.dimesions["time"].size
    idx = 0 if step is None else (step % steps)

    # load mesh payload
    data = ds.variables["hs"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleUnstructuredXY(lons, lats, lons.shape, data[idx], name, units, steps)

    return sample


def ww3_global_tri() -> SampleUnstructuredXY:
    """
    Load the WAVEWATCH III (WW3) unstructured triangular mesh.

    Returns
    -------
    SampleUnstructuredXY
        The unstructured spatial coordinates and data payload.

    Notes
    -----
    .. versionadded:: 0.1.0

    """
    fname = "ww3_gbl_tri_hs.nc"
    processor = pooch.Decompress(method="auto", name=fname)
    resource = CACHE.fetch(f"samples/ww3/{fname}.bz2", processor=processor)
    ds = nc.Dataset(resource)

    # load the lon/lat points
    lons = ds.variables["longitude"][:]
    lats = ds.variables["latitude"][:]

    # load the connectivity
    offset = 1  # minimum connectivity index offset
    connectivity = ds.variables["tri"][:] - offset

    # we know this is a single step timeseries, a priori
    idx = 0

    # load mesh payload
    data = ds.variables["hs"]
    name = capitalise(data.standard_name)
    units = data.units

    sample = SampleUnstructuredXY(lons, lats, connectivity, data[idx], name, units)

    return sample
